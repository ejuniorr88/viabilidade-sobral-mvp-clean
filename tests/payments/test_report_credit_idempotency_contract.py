from __future__ import annotations

from core import checkout_flow
import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_build_report_signature():
    fake_streamlit = types.SimpleNamespace(
        session_state={},
        cache_resource=lambda **_kwargs: (lambda fn: fn),
    )
    fake_supabase = types.SimpleNamespace(
        Client=object,
        create_client=lambda *args, **kwargs: object(),
    )

    old_streamlit = sys.modules.get("streamlit")
    old_supabase = sys.modules.get("supabase")
    sys.modules["streamlit"] = fake_streamlit
    sys.modules["supabase"] = fake_supabase
    try:
        spec = importlib.util.spec_from_file_location("client_reports_signature_under_test", ROOT / "core" / "client_reports.py")
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.build_report_signature
    finally:
        if old_streamlit is not None:
            sys.modules["streamlit"] = old_streamlit
        else:
            sys.modules.pop("streamlit", None)
        if old_supabase is not None:
            sys.modules["supabase"] = old_supabase
        else:
            sys.modules.pop("supabase", None)


def test_existing_report_is_loaded_without_new_credit_debit() -> None:
    events: list[str] = []
    session_state = {"auth_user_email": "teste@example.com"}

    def generate_report_pdf_bytes_func(*, calc, session_state):
        events.append("pdf")
        return b"pdf"

    def consume_viability_credit_func(**kwargs):
        events.append("consume")
        return {"ok": True, "new_balance": 4}

    def refund_viability_credit_func(**kwargs):
        events.append("refund")
        return {"ok": True, "new_balance": 5}

    def save_client_report_func(**kwargs):
        events.append("save")
        return {"ok": True, "already_exists": False, "row": {"id": "new"}}

    def get_existing_client_report_func(user_id, report_signature):
        events.append(f"lookup:{user_id}:{report_signature}")
        return {"id": "existing", "report_signature": report_signature}

    def commit_report_snapshot_func(calc_ref, session_snapshot, pdf_bytes, report_signature):
        events.append(f"commit:{report_signature}")

    result, pdf = checkout_flow.prepare_and_consume_report(
        calc_ref={"use_type_code": "RES_UNI", "zone": "ZAP"},
        session_snapshot={"lot_area_m2": 300},
        report_signature="sig-existing",
        user_id_value="user-1",
        selected_use_label_value="Residencial unifamiliar",
        categoria_label_value="Residencial",
        session_state=session_state,
        generate_report_pdf_bytes_func=generate_report_pdf_bytes_func,
        consume_viability_credit_func=consume_viability_credit_func,
        refund_viability_credit_func=refund_viability_credit_func,
        save_client_report_func=save_client_report_func,
        commit_report_snapshot_func=commit_report_snapshot_func,
        get_existing_client_report_func=get_existing_client_report_func,
    )

    assert pdf == b"pdf"
    assert result["ok"] is True
    assert result["already_exists"] is True
    assert result["already_saved_before_debit"] is True
    assert "consume" not in events
    assert "refund" not in events
    assert "save" not in events
    assert events == ["lookup:user-1:sig-existing", "pdf", "commit:sig-existing"]
    assert session_state["last_saved_report_signature"] == "sig-existing"


def test_new_report_debits_once_then_saves_and_commits() -> None:
    events: list[str] = []

    def generate_report_pdf_bytes_func(*, calc, session_state):
        events.append("pdf")
        return b"pdf"

    def consume_viability_credit_func(**kwargs):
        events.append(f"consume:{kwargs.get('idempotency_key')}")
        return {"ok": True, "new_balance": 3}

    def refund_viability_credit_func(**kwargs):
        events.append("refund")
        return {"ok": True, "new_balance": 4}

    def save_client_report_func(**kwargs):
        events.append(f"save:{kwargs.get('report_signature')}")
        return {"ok": True, "already_exists": False, "row": {"id": "new"}}

    def commit_report_snapshot_func(calc_ref, session_snapshot, pdf_bytes, report_signature):
        events.append(f"commit:{report_signature}")

    result, _ = checkout_flow.prepare_and_consume_report(
        calc_ref={"use_type_code": "RES_UNI", "zone": "ZAP"},
        session_snapshot={"lot_area_m2": 300},
        report_signature="sig-new",
        user_id_value="user-1",
        selected_use_label_value="Residencial unifamiliar",
        categoria_label_value="Residencial",
        session_state={"auth_user_email": "teste@example.com"},
        generate_report_pdf_bytes_func=generate_report_pdf_bytes_func,
        consume_viability_credit_func=consume_viability_credit_func,
        refund_viability_credit_func=refund_viability_credit_func,
        save_client_report_func=save_client_report_func,
        commit_report_snapshot_func=commit_report_snapshot_func,
        get_existing_client_report_func=lambda user_id, sig: None,
    )

    assert result["ok"] is True
    assert events == [
        "pdf",
        "consume:report_debit:user-1:sig-new",
        "save:sig-new",
        "commit:sig-new",
    ]


def test_report_signature_changes_for_credit_sensitive_scenario_switches() -> None:
    build_report_signature = _load_build_report_signature()

    base_calc = {
        "use_type_code": "RES_MULTI_R21",
        "selected_use_label": "R2.1",
        "categoria_label": "Residencial",
        "zone": "ZAP",
        "street_name": "Rua Teste",
        "road_type": "via local",
        "selected_lat": -3.7,
        "selected_lon": -40.3,
    }
    base_session = {
        "lot_area_m2": 300,
        "built_ground_m2": 0,
        "permeable_area_m2": 0,
        "lot_front_m": 10,
        "lot_depth_m": 30,
        "lot_is_corner": False,
        "lot_is_midblock": True,
        "lot_is_irregular": False,
        "lot_type_label": "Meio de quadra",
    }

    sig_base = build_report_signature(base_calc, base_session)
    sig_area = build_report_signature(base_calc, {**base_session, "built_ground_m2": 150})
    sig_corner = build_report_signature(base_calc, {**base_session, "lot_is_corner": True, "lot_is_midblock": False, "lot_type_label": "Esquina"})
    sig_irregular = build_report_signature(base_calc, {**base_session, "lot_is_irregular": True, "lot_front_m": 0, "lot_depth_m": 0, "lot_type_label": "Terreno irregular"})
    sig_r3 = build_report_signature({**base_calc, "use_type_code": "RES_MULTI_R3", "selected_use_label": "R3"}, base_session)

    assert sig_base != sig_area, "Informar área pretendida precisa gerar nova assinatura financeira."
    assert sig_base != sig_corner, "Trocar meio de quadra por esquina precisa gerar nova assinatura financeira."
    assert sig_base != sig_irregular, "Trocar para terreno irregular precisa gerar nova assinatura financeira."
    assert sig_base != sig_r3, "Trocar R2 para R3 precisa gerar nova assinatura financeira."


def test_credit_module_does_not_skip_debit_based_only_on_old_ledger_row() -> None:
    text = (ROOT / "core" / "credits.py").read_text(encoding="utf-8", errors="ignore")
    consume_body = text.split("def consume_viability_credit(", 1)[1].split("def _list_auth_user_ids_by_email", 1)[0]
    assert "existing_debit = _find_existing_report_debit(" not in consume_body
    assert "already_consumed" not in consume_body
    assert 'table("client_reports")' not in consume_body
    assert ".table('client_reports')" not in consume_body
    assert 'supabase.rpc(\n            "consume_viability_credit"' in consume_body


def test_tag_latest_report_debit_prefers_new_untagged_debit_over_old_tagged_row() -> None:
    text = (ROOT / "core" / "credits.py").read_text(encoding="utf-8", errors="ignore")
    tag_body = text.split("def _tag_latest_report_debit(", 1)[1].split("def consume_viability_credit", 1)[0]
    assert "already_tagged = already_tagged or row" in tag_body
    assert "continue" in tag_body
    assert "target = row" in tag_body
    assert "merged_metadata = {**existing_metadata, **metadata_payload}" in tag_body
    assert '"idempotency_key": stable_prefix' in tag_body



def test_sql_hardening_enforces_unique_saved_report_signature() -> None:
    sql = (ROOT / "sql" / "credit_report_delivery_hardening.sql").read_text(encoding="utf-8", errors="ignore").lower()
    assert "create unique index if not exists client_reports_user_signature_unique" in sql
    assert "on public.client_reports (user_id, report_signature)" in sql
    assert "where report_signature is not null" in sql
    assert "credit_ledger_idempotency_key_unique" not in sql
    assert "create index if not exists credit_ledger_idempotency_key_idx" in sql
    assert "não é único" in sql or "nao é único" in sql or "não é unico" in sql


def test_refund_metadata_carries_debit_ledger_id_for_same_signature_retries() -> None:
    refunds: list[dict] = []

    def generate_report_pdf_bytes_func(*, calc, session_state):
        return b"pdf"

    def consume_viability_credit_func(**kwargs):
        return {"ok": True, "new_balance": 2, "ledger_tag_result": {"ok": True, "ledger_id": "debit-1"}}

    def refund_viability_credit_func(**kwargs):
        refunds.append(kwargs)
        return {"ok": True, "new_balance": 3}

    def save_client_report_func(**kwargs):
        raise RuntimeError("storage down")

    def commit_report_snapshot_func(*args, **kwargs):
        raise AssertionError("snapshot não deve ser liberado quando o armazenamento falha")

    try:
        checkout_flow.prepare_and_consume_report(
            calc_ref={"use_type_code": "RES_UNI", "zone": "ZAP"},
            session_snapshot={"lot_area_m2": 300},
            report_signature="sig-retry",
            user_id_value="user-1",
            selected_use_label_value="Residencial unifamiliar",
            categoria_label_value="Residencial",
            session_state={"auth_user_email": "teste@example.com"},
            generate_report_pdf_bytes_func=generate_report_pdf_bytes_func,
            consume_viability_credit_func=consume_viability_credit_func,
            refund_viability_credit_func=refund_viability_credit_func,
            save_client_report_func=save_client_report_func,
            commit_report_snapshot_func=commit_report_snapshot_func,
            get_existing_client_report_func=lambda user_id, sig: None,
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError("falha de armazenamento deveria levantar erro")

    assert len(refunds) == 1
    assert refunds[0]["reference_id"] == "sig-retry"
    assert refunds[0]["metadata"]["report_signature"] == "sig-retry"
    assert refunds[0]["metadata"]["debit_ledger_id"] == "debit-1"
    assert refunds[0]["metadata"]["stage"] == "save_client_report_exception"


def test_refund_credit_idempotency_prefers_specific_debit_ledger_id() -> None:
    text = (ROOT / "core" / "credits.py").read_text(encoding="utf-8", errors="ignore")
    body = text.split("def refund_viability_credit(", 1)[1].split("def _is_target_user_current_identity", 1)[0]
    assert 'metadata_payload.get("debit_ledger_id")' in body
    assert 'or metadata_payload.get("refund_scope")' in body
    assert 'or reference_key' in body
    assert 'refund_viability_credit:{user_id}:{refund_scope}:{int(amount)}' in body


def test_refund_metadata_uses_unique_attempt_scope_when_ledger_tag_fails() -> None:
    refunds: list[dict] = []

    def generate_report_pdf_bytes_func(*, calc, session_state):
        return b"pdf"

    def consume_viability_credit_func(**kwargs):
        # Simula débito efetuado, mas sem ledger_id rastreável por falha de marcação.
        return {"ok": True, "new_balance": 2, "ledger_tag_result": {"ok": False, "reason": "debit_row_not_found"}}

    def refund_viability_credit_func(**kwargs):
        refunds.append(kwargs)
        return {"ok": True, "new_balance": 3}

    def save_client_report_func(**kwargs):
        raise RuntimeError("storage down")

    def commit_report_snapshot_func(*args, **kwargs):
        raise AssertionError("snapshot não deve ser liberado quando o armazenamento falha")

    try:
        checkout_flow.prepare_and_consume_report(
            calc_ref={"use_type_code": "RES_UNI", "zone": "ZAP"},
            session_snapshot={"lot_area_m2": 300},
            report_signature="sig-retry-no-ledger-id",
            user_id_value="user-1",
            selected_use_label_value="Residencial unifamiliar",
            categoria_label_value="Residencial",
            session_state={"auth_user_email": "teste@example.com"},
            generate_report_pdf_bytes_func=generate_report_pdf_bytes_func,
            consume_viability_credit_func=consume_viability_credit_func,
            refund_viability_credit_func=refund_viability_credit_func,
            save_client_report_func=save_client_report_func,
            commit_report_snapshot_func=commit_report_snapshot_func,
            get_existing_client_report_func=lambda user_id, sig: None,
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError("falha de armazenamento deveria levantar erro")

    assert len(refunds) == 1
    metadata = refunds[0]["metadata"]
    assert metadata["report_signature"] == "sig-retry-no-ledger-id"
    assert "debit_ledger_id" not in metadata
    assert metadata["refund_scope"].startswith("report_debit_attempt:user-1:sig-retry-no-ledger-id:")
    assert metadata["debit_attempt_key"] == metadata["refund_scope"]
