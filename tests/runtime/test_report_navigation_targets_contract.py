from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_generated_report_navigation_target_keeps_block3_anchor_contract() -> None:
    text = _read(ROOT / "ui" / "runtime" / "report_navigation" / "generated.py")

    required = [
        '"report_generated_notice_context"',
        '"element_id": "report-generated-context-start"',
        '"behavior": "generated_context"',
        'arm_report_navigation_target(session_state, "report_generated_notice_context")',
    ]
    for item in required:
        assert item in text, f"generated.py perdeu o contrato crítico do bloco 3: {item}"


def test_report_section_keeps_block3_heading_anchor_order_contract() -> None:
    text = _read(ROOT / "ui" / "report" / "section.py")

    report_start = text.index('st.markdown(\'<div id="report-section-start"></div>\', unsafe_allow_html=True)')
    divider = text.index('st.markdown("---")', report_start)
    generated_anchor = text.index('st.markdown(\'<div id="report-generated-context-start"></div>\', unsafe_allow_html=True)', divider)
    heading = text.index('st.subheader("Relatório completo")', generated_anchor)

    assert report_start < divider < generated_anchor < heading, (
        "section.py perdeu a ordem crítica do bloco 3: a âncora do cenário gerado precisa "
        "ficar depois do divisor e antes do heading 'Relatório completo'."
    )
