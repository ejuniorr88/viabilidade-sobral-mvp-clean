from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_report_contract_must_keep_relatorio_hooks() -> None:
    relatorio_py = ROOT / "ui" / "relatorio.py"
    assert relatorio_py.exists(), "ui/relatorio.py não encontrado"

    txt = _read(relatorio_py)

    required_anchors = [
        "fetch_zone_description",
        "render_zone_description_section",
        "render_quadro_tecnico",
        "render_dicas_valiosas",
        "render_figuras_anexo_v",
    ]
    for anchor in required_anchors:
        assert anchor in txt, f"ui/relatorio.py perdeu a âncora crítica: {anchor}"


def test_pdf_contract_must_keep_current_pdf_generation_hooks() -> None:
    pdf_py = ROOT / "core" / "report_pdf.py"
    assert pdf_py.exists(), "core/report_pdf.py não encontrado"

    txt = _read(pdf_py)

    required_anchors = [
        "generate_report_pdf_bytes",
        "build_report_payload",
        "fetch_zone_desc",
        "render_item_04",
        "render_item_11",
        "render_figuras",
        "render_item_13",
        "Dicas valiosas",
        "render_item_16",
    ]
    for anchor in required_anchors:
        assert anchor in txt, f"core/report_pdf.py perdeu a âncora crítica: {anchor}"


def test_pdf_contract_must_keep_zone_description_integration() -> None:
    pdf_py = ROOT / "core" / "report_pdf.py"
    txt = _read(pdf_py)

    required_anchors = [
        "fetch_zone_description",
        "fetch_zone_desc",
        "description_text",
        "_parse_zone_description_parts",
        "_fallback_zone_description",
    ]
    for anchor in required_anchors:
        assert anchor in txt, f"Integração da descrição da zona sumiu do PDF: {anchor}"
