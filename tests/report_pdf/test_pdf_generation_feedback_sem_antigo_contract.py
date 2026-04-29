from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_pdf_buttons_show_generation_feedback_message():
    client_area = _read("ui/client_area.py")
    report_section = _read("ui/report/section.py")
    expected = "Gerando relatório, aguarde alguns segundos para fazer o download."

    assert expected in client_area
    assert expected in report_section
    assert "with st.spinner(" in client_area
    assert "with st.spinner(" in report_section


def test_legacy_pdf_buttons_are_not_rendered():
    client_area = _read("ui/client_area.py")
    report_section = _read("ui/report/section.py")

    assert "Baixar PDF salvo antigo" not in client_area
    assert "Baixar PDF técnico antigo" not in report_section
    assert "download_report_pdf_legacy" not in report_section
    assert "generate_report_pdf_bytes_func(calc=report_calc" not in report_section


def test_visual_pdf_still_generates_only_after_click():
    client_area = _read("ui/client_area.py")
    report_section = _read("ui/report/section.py")

    assert "st.button(\"📄 Gerar relatório em PDF\"" in client_area
    assert "st.button(\"📄 Gerar relatório em PDF\"" in report_section
    assert "generate_snapshot_pdf_bytes" in client_area
    assert "generate_snapshot_pdf_bytes" in report_section
