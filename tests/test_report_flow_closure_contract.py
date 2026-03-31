from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


streamlit_stub = types.ModuleType("streamlit")
streamlit_stub.session_state = {}
streamlit_stub.secrets = {}
streamlit_stub.cache_resource = lambda show_spinner=False: (lambda fn: fn)
sys.modules.setdefault("streamlit", streamlit_stub)

supabase_stub = types.ModuleType("supabase")
supabase_stub.Client = object
supabase_stub.create_client = lambda url, key: object()
sys.modules.setdefault("supabase", supabase_stub)

from core import report_confirmation as report_confirmation_core
from core.client_reports import build_report_signature


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8", errors="ignore")


def _base_calc() -> dict:
    return {
        "use_type_code": "RES_UNI",
        "selected_use_label": "Residencial Unifamiliar (Casa)",
        "categoria_label": "Residencial",
        "zone": "ZAM",
        "street_name": "Rua Teste",
        "road_type": "via local",
        "project_mode": "",
        "selected_lat": -3.72,
        "selected_lon": -40.34,
        "rule": {"ok": True},
    }


def _base_session() -> dict:
    return {
        "lot_area_m2": 300,
        "built_ground_m2": 120,
        "permeable_area_m2": 90,
        "lot_front_m": 10,
        "lot_depth_m": 30,
        "lot_is_corner": False,
        "lot_is_irregular": False,
    }


def test_generate_report_area_change_requires_confirmation_before_consumption() -> None:
    app_py = _read("app.py")

    required = [
        "elif has_snapshot and not is_same_as_snapshot:",
        "report_confirmation_core.arm_new_report_confirmation(",
        "current_report_session=deepcopy(current_report_session)",
        "current_report_signature=current_report_signature",
        "st.rerun()",
    ]
    for item in required:
        assert item in app_py, f"Fluxo de mudança de área perdeu a trava de confirmação: {item}"

    gerar_relatorio_block = app_py.split("if gerar_relatorio:", 1)[1][:2200]
    assert gerar_relatorio_block.index("elif has_snapshot and not is_same_as_snapshot:") < gerar_relatorio_block.index(
        "_prepare_and_consume_report("
    ), "A confirmação de novo relatório precisa acontecer antes do preparo/consumo do relatório."



def test_use_change_produces_new_report_signature_and_requires_new_report_confirmation() -> None:
    calc_snapshot = _base_calc()
    session_snapshot = _base_session()
    snapshot_signature = build_report_signature(calc_snapshot, session_snapshot)

    calc_current = _base_calc()
    calc_current["use_type_code"] = "RES_MULTI_R21"
    calc_current["selected_use_label"] = "Residencial Multifamiliar R2.1"

    session_state = {
        "report_snapshot_calc": dict(calc_snapshot),
        "report_snapshot_signature": snapshot_signature,
        **session_snapshot,
    }

    state = report_confirmation_core.compute_report_confirmation_state(
        calc_ref=calc_current,
        built_ground_value=session_snapshot["built_ground_m2"],
        permeable_area_value=session_snapshot["permeable_area_m2"],
        session_state=session_state,
        signature_builder=build_report_signature,
    )

    assert state["has_snapshot"] is True
    assert state["is_same_as_snapshot"] is False
    assert state["current_report_signature"] != snapshot_signature



def test_blocked_preview_preserves_credit_and_blocks_prepare_and_consume() -> None:
    app_py = _read("app.py")

    gerar_relatorio_block = app_py.split("if gerar_relatorio:", 1)[1][:2200]
    required = [
        "if preview_inadequado:",
        "_clear_report_runtime_state(preserve_snapshot=True)",
        'st.error("Este estudo está bloqueado por inadequabilidade. O crédito foi preservado.")',
    ]
    for item in required:
        assert item in gerar_relatorio_block, f"Fluxo inadequado perdeu a proteção de crédito: {item}"

    assert gerar_relatorio_block.index("if preview_inadequado:") < gerar_relatorio_block.index("_prepare_and_consume_report("), (
        "O bloqueio por preview inadequado precisa acontecer antes do preparo/consumo do relatório."
    )



def test_zero_balance_opens_inline_payments_before_prepare_and_consume() -> None:
    app_py = _read("app.py")

    gerar_relatorio_block = app_py.split("if gerar_relatorio:", 1)[1][:2400]
    required = [
        'elif saldo_atual is not None and int(saldo_atual) <= 0:',
        'st.session_state.show_inline_payments = True',
        'st.error("Você não possui créditos suficientes para gerar o relatório.")',
    ]
    for item in required:
        assert item in gerar_relatorio_block, f"Fluxo de saldo zero perdeu a abertura dos planos inline: {item}"

    assert gerar_relatorio_block.index('elif saldo_atual is not None and int(saldo_atual) <= 0:') < gerar_relatorio_block.index(
        "_prepare_and_consume_report("
    ), "Com saldo zero, o app precisa abrir os planos inline antes de qualquer preparo/consumo do relatório."



def test_calc_signature_change_reset_preserves_snapshot_and_pending_when_requested() -> None:
    app_py = _read("app.py")
    assert '_clear_report_runtime_state(preserve_snapshot=True, preserve_pending=True)' in app_py, (
        "Ao trocar a assinatura de cálculo, o app precisa preservar snapshot e pending no reset defensivo."
    )

    session_state = {
        "report_unlocked": True,
        "show_inline_payments": True,
        "last_generated_pdf_bytes": b"pdf",
        "last_generated_pdf_signature": "sig-current",
        "last_saved_report_signature": "sig-current",
        "report_snapshot_calc": {"use_type_code": "RES_UNI"},
        "report_snapshot_session": {"lot_area_m2": 300},
        "report_snapshot_signature": "sig-snapshot",
        "confirm_new_report": True,
        "pending_report_calc": {"use_type_code": "RES_MULTI_R21"},
        "pending_report_session": {"lot_area_m2": 300},
        "pending_report_signature": "sig-pending",
        "last_calc_signature": "calc-old",
    }

    report_confirmation_core.clear_report_runtime_state(
        session_state=session_state,
        preserve_snapshot=True,
        preserve_pending=True,
    )

    assert session_state["report_unlocked"] is False
    assert session_state["show_inline_payments"] is False
    assert session_state["last_generated_pdf_bytes"] is None
    assert session_state["report_snapshot_signature"] == "sig-snapshot"
    assert session_state["pending_report_signature"] == "sig-pending"
    assert session_state["confirm_new_report"] is True
