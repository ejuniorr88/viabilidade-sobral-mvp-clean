from __future__ import annotations

"""
Núcleo protegido de entrega do relatório pago.

Regra de arquitetura:
- UI não deve debitar crédito diretamente.
- UI não deve salvar relatório diretamente em client_reports.
- UI deve chamar esta fachada para a entrega final do relatório.

Este módulo concentra a orquestração sensível sem alterar a lógica consolidada
em checkout_flow, credits, client_reports, payments e report_pdf.
"""

from typing import Any, Dict, MutableMapping

from core import checkout_flow as checkout_flow_core
from core.client_reports import build_report_signature, get_client_report_by_signature, save_client_report
from core.credits import consume_viability_credit, get_credit_balance, refund_viability_credit
from core.payments import ensure_paid_payment_is_credited, refresh_payment_status_and_credit
from core.report_pdf import generate_report_pdf_bytes


def _pick_delivery_value(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and value.strip() == "":
            continue
        return value
    return None


def live_report_signature_coords(*, session_state: MutableMapping[str, Any], calc_ref: Dict[str, Any] | None = None) -> tuple[Any, Any]:
    """Coordenadas para a assinatura viva da tela antes do recálculo.

    Neste ponto, o usuário pode ter clicado em outro lote, mas ``calc`` ainda
    pode carregar o resultado anterior. Por isso ``last_click`` prevalece;
    ``calc`` e campos legados entram apenas como fallback.
    """
    calc_source = calc_ref if isinstance(calc_ref, dict) else session_state.get("calc")
    calc_source = calc_source if isinstance(calc_source, dict) else {}

    last_click = session_state.get("last_click")
    click_lat = click_lon = None
    if isinstance(last_click, dict):
        click_lat = last_click.get("lat")
        click_lon = last_click.get("lon")

    lat = _pick_delivery_value(
        click_lat,
        calc_source.get("lat"),
        calc_source.get("selected_lat"),
        session_state.get("lat"),
        session_state.get("selected_lat"),
    )
    lon = _pick_delivery_value(
        click_lon,
        calc_source.get("lon"),
        calc_source.get("selected_lon"),
        session_state.get("lon"),
        session_state.get("selected_lon"),
    )
    return lat, lon


def build_report_delivery_signature(*, calc: Dict[str, Any], session_state: Dict[str, Any]) -> str:
    """Assinatura oficial usada pelo fluxo de entrega/salvamento do relatório."""
    return build_report_signature(calc=calc, session_state=session_state)


def preflight_report_delivery_credit_balance(
    user_id_value: str | None,
    *,
    session_state: MutableMapping[str, Any],
) -> int:
    """Reconcilia pagamentos pendentes e retorna o saldo antes de liberar relatório."""
    return checkout_flow_core.preflight_report_credit_balance(
        user_id_value,
        session_state=session_state,
        get_credit_balance_func=get_credit_balance,
        refresh_payment_status_and_credit_func=refresh_payment_status_and_credit,
        ensure_paid_payment_is_credited_func=ensure_paid_payment_is_credited,
    )


def deliver_paid_report(
    *,
    calc_ref: Dict[str, Any],
    session_snapshot: Dict[str, Any],
    report_signature: str,
    user_id_value: str | None,
    selected_use_label_value: str,
    categoria_label_value: str,
    session_state: MutableMapping[str, Any],
    commit_report_snapshot_func,
) -> tuple[Dict[str, Any], bytes]:
    """Entrega oficial do relatório pago.

    Esta é a única fachada que a tela deve usar para o fluxo sensível:
    gerar PDF, consumir crédito, salvar em client_reports/Storage,
    estornar se falhar e consolidar snapshot.
    """
    preflight_credit_balance = lambda *, user_id_value: preflight_report_delivery_credit_balance(
        user_id_value,
        session_state=session_state,
    )

    return checkout_flow_core.prepare_and_consume_report(
        calc_ref=calc_ref,
        session_snapshot=session_snapshot,
        report_signature=report_signature,
        user_id_value=user_id_value,
        selected_use_label_value=selected_use_label_value,
        categoria_label_value=categoria_label_value,
        session_state=session_state,
        generate_report_pdf_bytes_func=generate_report_pdf_bytes,
        consume_viability_credit_func=consume_viability_credit,
        refund_viability_credit_func=refund_viability_credit,
        commit_report_snapshot_func=commit_report_snapshot_func,
        save_client_report_func=save_client_report,
        get_existing_client_report_func=get_client_report_by_signature,
        preflight_reconcile_credit_func=preflight_credit_balance,
    )
