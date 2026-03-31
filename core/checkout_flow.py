from __future__ import annotations

from typing import Any, MutableMapping


def prepare_and_consume_report(*, calc_ref, session_snapshot, report_signature, user_id_value, selected_use_label_value, categoria_label_value, session_state: MutableMapping[str, Any], generate_report_pdf_bytes_func, consume_viability_credit_func, commit_report_snapshot_func, save_client_report_func):
    pdf_bytes = generate_report_pdf_bytes_func(calc=calc_ref, session_state=session_snapshot)
    debit_result = consume_viability_credit_func(
        user_id=user_id_value,
        amount=1,
        description="Geração de relatório de viabilidade",
    )
    if not debit_result.get("ok"):
        raise RuntimeError(debit_result.get("message") or "Saldo insuficiente para gerar o relatório.")
    commit_report_snapshot_func(calc_ref, session_snapshot, pdf_bytes, report_signature)
    try:
        if session_state.get("last_saved_report_signature") != report_signature:
            save_result = save_client_report_func(
                user_id=user_id_value,
                user_email=session_state.get("auth_user_email") or "",
                calc={**calc_ref, "selected_use_label": selected_use_label_value, "categoria_label": categoria_label_value},
                session_state=session_snapshot,
                pdf_bytes=pdf_bytes,
                report_signature=report_signature,
            )
            if save_result.get("ok"):
                session_state["last_saved_report_signature"] = report_signature
    except Exception:
        pass
    return debit_result, pdf_bytes
