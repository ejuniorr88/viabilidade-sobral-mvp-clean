from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")



def test_report_section_keeps_pdf_download_button_contract() -> None:
    text = _read(ROOT / "ui" / "report" / "section.py")

    required = [
        'st.markdown("### Download do relatório")',
        'generate_report_pdf_bytes_func(calc=report_calc, session_state=report_session)',
        'st.download_button(',
        'label="⬇️ Baixar relatório em PDF"',
        'file_name="relatorio_viabilidade.pdf"',
        'mime="application/pdf"',
        'key="download_report_pdf"',
    ]
    for item in required:
        assert item in text, f"ui/report/section.py perdeu âncora crítica do download do PDF: {item}"
