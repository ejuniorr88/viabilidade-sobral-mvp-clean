from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_app_delegates_report_section_to_new_module() -> None:
    text = _read(ROOT / "app.py")

    required = [
        "from ui.report.section import render_report_section",
        "render_report_section(",
        "can_offer_report=can_offer_report",
        "preview_inadequado=preview_inadequado",
    ]
    for item in required:
        assert item in text, f"app.py deixou de delegar a seção de relatório para o novo módulo: {item}"


def test_new_report_module_keeps_main_visual_anchors() -> None:
    text = _read(ROOT / "ui" / "report" / "section.py")

    required = [
        'st.subheader("Relatório completo")',
        '"📄 Gerar relatório"',
        'key="btn_generate_report"',
        'render_zone_description_section_func(report_calc)',
        'render_relatorio_section_func(report_calc)',
        'key="download_report_pdf"',
    ]
    for item in required:
        assert item in text, f"ui/report/section.py perdeu âncora visual crítica do relatório: {item}"
