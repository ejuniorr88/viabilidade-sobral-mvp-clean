from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")



def test_report_section_keeps_generate_button_and_runtime_entrypoints() -> None:
    text = _read(ROOT / "ui" / "report" / "section.py")

    required = [
        'st.subheader("Relatório completo")',
        '"📄 Gerar relatório"',
        'key="btn_generate_report"',
        'disabled=(not user_logged_in)',
        'compute_report_confirmation_state_func(',
        'prepare_and_consume_report_func(',
        'build_current_report_signature_func',
        'arm_new_report_confirmation_func(',
    ]
    for item in required:
        assert item in text, f"ui/report/section.py perdeu âncora crítica do runtime do relatório: {item}"
