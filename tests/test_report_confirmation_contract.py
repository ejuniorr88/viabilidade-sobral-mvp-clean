from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8", errors="ignore")


def test_app_keeps_report_confirmation_runtime_functions() -> None:
    app_py = _read("app.py")

    required = [
        "def _current_report_session_snapshot(",
        "def _commit_report_snapshot(",
        "def _clear_pending_report(",
        "def _clear_report_runtime_state(",
        "def _prepare_and_consume_report(",
    ]
    for item in required:
        assert item in app_py, f"app.py perdeu função crítica da confirmação de relatório: {item}"


def test_app_keeps_preview_block_and_runtime_reset_calls() -> None:
    app_py = _read("app.py")

    required = [
        "preview_inadequado = _should_block_report_preview(calc)",
        "if preview_inadequado:",
        "_clear_report_runtime_state(preserve_snapshot=True)",
        "_render_blocked_report_preview(calc)",
    ]
    for item in required:
        assert item in app_py, f"app.py perdeu trava principal da confirmação/preview: {item}"


def test_app_keeps_pending_confirmation_flow() -> None:
    app_py = _read("app.py")

    required = [
        "if gerar_relatorio:",
        "elif has_snapshot and not is_same_as_snapshot:",
        "report_confirmation_core.arm_new_report_confirmation(",
        'if st.session_state.get("confirm_new_report") and st.session_state.get("pending_report_signature"):',
        'confirm_yes = st.button("Sim, gerar outro relatório"',
        'confirm_no = st.button("Não"',
    ]
    for item in required:
        assert item in app_py, f"app.py perdeu etapa crítica do fluxo de confirmação de novo relatório: {item}"


def test_app_keeps_snapshot_comparison_for_existing_report() -> None:
    app_py = _read("app.py")

    required = [
        "report_confirmation_state = report_confirmation_core.compute_report_confirmation_state(",
        'current_report_session = report_confirmation_state["current_report_session"]',
        'current_report_signature = report_confirmation_state["current_report_signature"]',
        'snapshot_signature = report_confirmation_state["snapshot_signature"]',
        'has_snapshot = report_confirmation_state["has_snapshot"]',
        'is_same_as_snapshot = report_confirmation_state["is_same_as_snapshot"]',
    ]
    for item in required:
        assert item in app_py, f"app.py perdeu comparação do relatório atual com o snapshot anterior: {item}"


def test_client_reports_signature_covers_relevant_report_inputs() -> None:
    client_reports = _read("core/client_reports.py")

    required = [
        '"use_type_code"',
        '"project_mode"',
        '"lot_area_m2"',
        '"built_ground_m2"',
        '"permeable_area_m2"',
        '"lot_front_m"',
        '"lot_depth_m"',
        '"lot_is_corner"',
        '"lot_is_irregular"',
        '"selected_lat"',
        '"selected_lon"',
    ]
    for item in required:
        assert item in client_reports, f"core/client_reports.py perdeu campo crítico da assinatura do relatório: {item}"
