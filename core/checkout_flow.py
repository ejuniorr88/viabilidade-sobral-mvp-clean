from __future__ import annotations

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
    commit_report_snapshot_func,
    save_client_report_func,
    preflight_reconcile_credit_func=None,
):
    if preflight_reconcile_credit_func is not None:
        try:
            preflight_reconcile_credit_func(user_id_value=user_id_value)
        except Exception as e:
            session_state["last_report_credit_preflight_error"] = str(e)

    pdf_bytes = generate_report_pdf_bytes_func(calc=calc_ref, session_state=session_snapshot)

    debit_result = consume_viability_credit_func(
        user_id=user_id_value,
        amount=1,
        description="Geração de relatório de viabilidade",
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
            metadata={"report_signature": report_signature, "stage": "save_client_report_exception"},
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
            metadata={"report_signature": report_signature, "stage": "already_exists"},
        )
        session_state["last_report_refund_result"] = refund_result
        session_state["last_saved_report_signature"] = report_signature
        commit_report_snapshot_func(calc_ref, session_snapshot, pdf_bytes, report_signature)
        return debit_result, pdf_bytes

    if save_result and save_result.get("ok"):
        session_state["last_saved_report_signature"] = report_signature

    commit_report_snapshot_func(calc_ref, session_snapshot, pdf_bytes, report_signature)
    session_state["last_report_storage_error"] = None
    return debit_result, pdf_bytes
