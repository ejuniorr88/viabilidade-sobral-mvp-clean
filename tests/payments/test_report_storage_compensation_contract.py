from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_checkout_flow_keeps_refund_markers_for_storage_failure_or_duplicate() -> None:
    text = _read(ROOT / "core" / "checkout_flow.py")
    required = [
        'refund_viability_credit_func(',
        'last_report_storage_error',
        'last_report_refund_result',
        'already_exists',
        'Área do Cliente',
    ]
    for item in required:
        assert item in text, (
            "checkout_flow deve manter compensação explícita quando falhar o armazenamento "
            f"ou quando o relatório já existir: {item}"
        )


def test_report_section_keeps_user_visible_failure_feedback() -> None:
    text = _read(ROOT / "ui" / "report" / "section.py")
    required = [
        'st.error(f"Não foi possível preparar e gerar o relatório: {e}")',
        'st.error(f"Não foi possível preparar e gerar o novo relatório: {e}")',
    ]
    for item in required:
        assert item in text, (
            "A UI do relatório deve manter retorno visível ao usuário quando o preparo/armazenamento falhar: "
            f"{item}"
        )
