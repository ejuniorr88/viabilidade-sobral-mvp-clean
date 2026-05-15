from __future__ import annotations

from core import checkout_flow


def test_checkout_flow_reconciles_recent_paid_payment_before_consuming_credit() -> None:
    events: list[str] = []

    def preflight(*, user_id_value):
        events.append(f"preflight:{user_id_value}")
        return 1

    def generate_report_pdf_bytes_func(*, calc, session_state):
        events.append("pdf")
        return b"pdf"

    def consume_viability_credit_func(*, user_id, amount, description, **_kwargs):
        events.append(f"consume:{user_id}:{amount}")
        return {"ok": True, "new_balance": 0}

    def refund_viability_credit_func(**kwargs):
        events.append("refund")
        return {"ok": True}

    def commit_report_snapshot_func(calc_ref, session_snapshot, pdf_bytes, report_signature):
        events.append(f"commit:{report_signature}")

    def save_client_report_func(**kwargs):
        events.append("save")
        return {"ok": True, "already_exists": False, "row": {"id": "row-1"}}

    session_state = {"auth_user_email": "user@example.com"}

    debit_result, pdf_bytes = checkout_flow.prepare_and_consume_report(
        calc_ref={"zone": "ZAM"},
        session_snapshot={"lot_area_m2": 100},
        report_signature="sig-1",
        user_id_value="user-1",
        selected_use_label_value="Residencial",
        categoria_label_value="Residencial",
        session_state=session_state,
        generate_report_pdf_bytes_func=generate_report_pdf_bytes_func,
        consume_viability_credit_func=consume_viability_credit_func,
        refund_viability_credit_func=refund_viability_credit_func,
        commit_report_snapshot_func=commit_report_snapshot_func,
        save_client_report_func=save_client_report_func,
        preflight_reconcile_credit_func=preflight,
    )

    assert debit_result["ok"] is True
    assert pdf_bytes == b"pdf"
    assert events == [
        "preflight:user-1",
        "pdf",
        "consume:user-1:1",
        "save",
        "commit:sig-1",
    ]


def test_checkout_flow_records_preflight_error_but_keeps_report_flow_alive() -> None:
    session_state = {"auth_user_email": "user@example.com"}

    def preflight(*, user_id_value):
        raise RuntimeError("gateway slow")

    debit_result, pdf_bytes = checkout_flow.prepare_and_consume_report(
        calc_ref={"zone": "ZAM"},
        session_snapshot={"lot_area_m2": 100},
        report_signature="sig-2",
        user_id_value="user-1",
        selected_use_label_value="Residencial",
        categoria_label_value="Residencial",
        session_state=session_state,
        generate_report_pdf_bytes_func=lambda **kwargs: b"pdf",
        consume_viability_credit_func=lambda **kwargs: {"ok": True, "new_balance": 0},
        refund_viability_credit_func=lambda **kwargs: {"ok": True},
        commit_report_snapshot_func=lambda *args, **kwargs: None,
        save_client_report_func=lambda **kwargs: {"ok": True, "already_exists": False, "row": {"id": "row-1"}},
        preflight_reconcile_credit_func=preflight,
    )

    assert debit_result["ok"] is True
    assert pdf_bytes == b"pdf"
    assert session_state["last_report_credit_preflight_error"] == "gateway slow"
