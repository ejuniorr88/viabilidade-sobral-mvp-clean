from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8", errors="ignore")


def test_app_keeps_wrappers_for_report_confirmation_logic() -> None:
    app_py = _read("app.py")

    required = [
        "from core import report_confirmation as report_confirmation_core",
        "def _current_report_session_snapshot(",
        "def _commit_report_snapshot(",
        "def _clear_pending_report(",
        "def _clear_report_runtime_state(",
        "return report_confirmation_core.current_report_session_snapshot(",
        "report_confirmation_core.commit_report_snapshot(",
        "report_confirmation_core.clear_pending_report(",
        "report_confirmation_core.clear_report_runtime_state(",
    ]
    for item in required:
        assert item in app_py, f"app.py perdeu a blindagem por wrapper da confirmação de relatório: {item}"


def test_app_uses_report_confirmation_core_for_signature_state_and_pending() -> None:
    app_py = _read("app.py")

    required = [
        "report_confirmation_core.build_calc_signature(",
        "report_confirmation_core.compute_report_confirmation_state(",
        "report_confirmation_core.arm_new_report_confirmation(",
        "current_report_session = report_confirmation_state[\"current_report_session\"]",
        "current_report_signature = report_confirmation_state[\"current_report_signature\"]",
        "snapshot_signature = report_confirmation_state[\"snapshot_signature\"]",
        "has_snapshot = report_confirmation_state[\"has_snapshot\"]",
        "is_same_as_snapshot = report_confirmation_state[\"is_same_as_snapshot\"]",
    ]
    for item in required:
        assert item in app_py, f"app.py perdeu a integração com core/report_confirmation.py: {item}"


def test_report_confirmation_module_keeps_core_functions() -> None:
    module_txt = _read("core/report_confirmation.py")

    required = [
        "def current_report_session_snapshot(",
        "def commit_report_snapshot(",
        "def clear_pending_report(",
        "def clear_report_runtime_state(",
        "def build_calc_signature(",
        "def compute_report_confirmation_state(",
        "def arm_new_report_confirmation(",
        "signature_builder(calc_ref, current_report_session)",
        "preserve_pending: bool = False",
    ]
    for item in required:
        assert item in module_txt, f"core/report_confirmation.py perdeu peça crítica da blindagem: {item}"
