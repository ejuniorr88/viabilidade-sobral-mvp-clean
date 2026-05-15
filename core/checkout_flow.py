from __future__ import annotations

import uuid
from typing import Any, Callable, MutableMapping


def preflight_report_credit_balance(
    user_id_value: str | None,
    *,
    session_state: MutableMapping[str, Any],
    get_credit_balance_func: Callable[[str], Any],
    refresh_payment_status_and_credit_func: Callable[..., dict],
    ensure_paid_payment_is_credited_func: Callable[..., dict],
):
    if not user_id_value:
        return 0

    payment_id = session_state.get("current_payment_id")
    if payment_id:
        payment_id = str(payment_id)
        try:
            refresh_result = refresh_payment_status_and_credit_func(
                payment_id=payment_id,
                target_user_id=user_id_value,
            )
            payment_row = (refresh_result or {}).get("payment") or {}
            payment_status = str(payment_row.get("status") or "").strip().lower()
            latest_payment = payment_row

            if payment_status == "paid":
                ensure_result = ensure_paid_payment_is_credited_func(
                    payment_id=payment_id,
                    target_user_id=user_id_value,
                )
                latest_payment = (ensure_result or {}).get("payment") or payment_row
                if bool((ensure_result or {}).get("fully_credited")):
                    session_state["payments_focus_mode"] = False

            merged_payment = dict(session_state.get("current_payment_snapshot") or {})
            if isinstance(latest_payment, dict):
                merged_payment.update(latest_payment)
            if merged_payment:
                session_state["current_payment_snapshot"] = merged_payment
                session_state["current_payment_id"] = merged_payment.get("id", payment_id)
        except Exception as e:
            session_state["last_report_credit_preflight_error"] = str(e)

    fresh_balance = get_credit_balance_func(user_id_value)
    session_state["last_report_credit_preflight_balance"] = fresh_balance
    return fresh_balance


def _already_saved_result(*, report_signature: str, existing_report: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "ok": True,
        "already_exists": True,
        "already_saved_before_debit": True,
        "row": existing_report or {},
        "new_balance": None,
        "message": "Este relatório já estava salvo na Área do Cliente. Nenhum novo crédito foi consumido.",
        "report_signature": report_signature,
    }


def _refund_metadata(
    *,
    report_signature: str,
    stage: str,
    debit_result: dict[str, Any],
    debit_attempt_key: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "report_signature": report_signature,
        "stage": stage,
        "debit_attempt_key": debit_attempt_key,
    }
    ledger_tag = debit_result.get("ledger_tag_result") if isinstance(debit_result, dict) else None
    if isinstance(ledger_tag, dict) and ledger_tag.get("ledger_id"):
        metadata["debit_ledger_id"] = str(ledger_tag.get("ledger_id"))
    else:
        # Blindagem crítica: se a RPC antiga debitou mas a marcação do ledger
        # falhou/não achou a linha, o estorno não pode voltar a usar só a
        # assinatura do relatório. Cada débito real recebe uma tentativa única,
        # evitando que um estorno antigo do mesmo relatório bloqueie outro.
        metadata["refund_scope"] = debit_attempt_key
    if isinstance(extra, dict):
        metadata.update(extra)
    return metadata


def prepare_and_consume_report(
    *,
    calc_ref,
    session_snapshot,
    report_signature,
    user_id_value,
    selected_use_label_value,
    categoria_label_value,
    session_state: MutableMapping[str, Any],
    generate_report_pdf_bytes_func,
    consume_viability_credit_func,
    refund_viability_credit_func,
    save_client_report_func,
    commit_report_snapshot_func,
    get_existing_client_report_func=None,
    preflight_reconcile_credit_func=None,
):
    """Gera, debita e salva o relatório pago com compensação financeira.

    Ordem protegida:
    1. reconcilia saldo/pagamentos;
    2. se o mesmo report_signature já está salvo, não debita de novo;
    3. gera PDF;
    4. debita 1 crédito com chave idempotente por assinatura;
    5. salva na Área do Cliente;
    6. se o salvamento falhar, estorna automaticamente;
    7. só então libera o snapshot local.
    """
    if preflight_reconcile_credit_func is not None:
        try:
            preflight_reconcile_credit_func(user_id_value=user_id_value)
        except Exception as e:
            session_state["last_report_credit_preflight_error"] = str(e)

    existing_before_debit = None
    if get_existing_client_report_func is not None and user_id_value and report_signature:
        try:
            existing_before_debit = get_existing_client_report_func(user_id_value, report_signature)
        except Exception as e:
            # Não bloqueia a geração se a consulta de duplicidade falhar; o save final
            # ainda tem proteção com estorno. Guardamos o erro para auditoria.
            session_state["last_report_existing_lookup_error"] = str(e)

    if existing_before_debit:
        pdf_bytes = generate_report_pdf_bytes_func(calc=calc_ref, session_state=session_snapshot)
        snapshot_committer = commit_report_snapshot_func
        snapshot_committer(calc_ref, session_snapshot, pdf_bytes, report_signature)
        session_state["last_saved_report_signature"] = report_signature
        session_state["last_report_storage_error"] = None
        return _already_saved_result(report_signature=report_signature, existing_report=existing_before_debit), pdf_bytes

    pdf_bytes = generate_report_pdf_bytes_func(calc=calc_ref, session_state=session_snapshot)

    debit_attempt_key = f"report_debit_attempt:{user_id_value}:{report_signature}:{uuid.uuid4().hex}"
    debit_result = consume_viability_credit_func(
        user_id=user_id_value,
        amount=1,
        description="Geração de relatório de viabilidade",
        reference_id=report_signature,
        idempotency_key=f"report_debit:{user_id_value}:{report_signature}",
        metadata={
            "report_signature": report_signature,
            "stage": "report_generation_debit",
            "debit_attempt_key": debit_attempt_key,
        },
    )
    if not debit_result.get("ok"):
        raise RuntimeError(debit_result.get("message") or "Saldo insuficiente para gerar o relatório.")

    save_result = None
    try:
        save_result = save_client_report_func(
            user_id=user_id_value,
            user_email=session_state.get("auth_user_email") or "",
            calc={**calc_ref, "selected_use_label": selected_use_label_value, "categoria_label": categoria_label_value},
            session_state=session_snapshot,
            pdf_bytes=pdf_bytes,
            report_signature=report_signature,
        )
    except Exception as e:
        refund_result = refund_viability_credit_func(
            user_id=user_id_value,
            amount=1,
            description="Estorno automático por falha ao armazenar relatório",
            reference_id=report_signature,
            metadata=_refund_metadata(
                report_signature=report_signature,
                stage="save_client_report_exception",
                debit_result=debit_result,
                debit_attempt_key=debit_attempt_key,
            ),
        )
        session_state["last_report_storage_error"] = str(e)
        session_state["last_report_refund_result"] = refund_result
        raise RuntimeError(f"Falha ao armazenar o relatório na Área do Cliente: {e}")

    if save_result and save_result.get("already_exists"):
        refund_result = refund_viability_credit_func(
            user_id=user_id_value,
            amount=1,
            description="Estorno automático por relatório já armazenado",
            reference_id=report_signature,
            metadata=_refund_metadata(
                report_signature=report_signature,
                stage="already_exists",
                debit_result=debit_result,
                debit_attempt_key=debit_attempt_key,
            ),
        )
        session_state["last_report_refund_result"] = refund_result
        session_state["last_saved_report_signature"] = report_signature
        commit_report_snapshot_func(calc_ref, session_snapshot, pdf_bytes, report_signature)
        return {
            **debit_result,
            "ok": True,
            "already_exists": True,
            "refunded": True,
            "refund_result": refund_result,
            "new_balance": refund_result.get("new_balance", debit_result.get("new_balance")),
            "message": "Este relatório já estava salvo na Área do Cliente. O crédito foi estornado automaticamente.",
        }, pdf_bytes

    if save_result and save_result.get("ok"):
        session_state["last_saved_report_signature"] = report_signature
    else:
        refund_result = refund_viability_credit_func(
            user_id=user_id_value,
            amount=1,
            description="Estorno automático por relatório não confirmado na Área do Cliente",
            reference_id=report_signature,
            metadata=_refund_metadata(
                report_signature=report_signature,
                stage="save_client_report_not_ok",
                debit_result=debit_result,
                debit_attempt_key=debit_attempt_key,
                extra={"save_result": save_result},
            ),
        )
        session_state["last_report_refund_result"] = refund_result
        session_state["last_report_storage_error"] = "Relatório não confirmado na Área do Cliente."
        raise RuntimeError("Falha ao confirmar o relatório na Área do Cliente. O crédito foi estornado automaticamente.")

    commit_report_snapshot_func(calc_ref, session_snapshot, pdf_bytes, report_signature)
    session_state["last_report_storage_error"] = None
    return debit_result, pdf_bytes
