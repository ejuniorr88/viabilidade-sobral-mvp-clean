from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_report_pdf_keeps_dicas_valiosas_section() -> None:
    pdf_py = _read(ROOT / "core" / "report_pdf.py")

    required = [
        'def render_item_13',
        'Dicas valiosas',
        'Flexibilidade de recuos',
        'Calçada',
        'Piscina',
        'Art. 144',
    ]
    for item in required:
        assert item in pdf_py, f"core/report_pdf.py perdeu a seção consolidada de Dicas Valiosas: {item}"


def test_report_pdf_accepts_current_dicas_valiosas_card_contract() -> None:
    pdf_py = _read(ROOT / "core" / "report_pdf.py")

    assert 'card_box(pdf, "1. Flexibilidade de recuos"' in pdf_py
    assert 'card_box(pdf, "2. Calçada"' in pdf_py
    assert 'card_box(pdf, "3. Piscina e TO"' in pdf_py
    assert 'card_box(pdf, "4. Art. 144 e leitura prática"' in pdf_py
