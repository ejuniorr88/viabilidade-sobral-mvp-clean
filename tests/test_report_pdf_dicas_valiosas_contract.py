from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")



def test_report_pdf_keeps_dicas_valiosas_integration() -> None:
    pdf_py = _read(ROOT / "core" / "report_pdf.py")

    required = [
        'get_dicas_valiosas',
        '_render_dicas_valiosas',
    ]
    for item in required:
        assert item in pdf_py, f"core/report_pdf.py perdeu a integração crítica das Dicas Valiosas: {item}"



def test_report_pdf_accepts_current_dicas_valiosas_iteration_contract() -> None:
    pdf_py = _read(ROOT / "core" / "report_pdf.py")

    assert (
        'for dica in get_dicas_valiosas(' in pdf_py
        or 'for titulo, texto in get_dicas_valiosas(' in pdf_py
        or 'for item in get_dicas_valiosas(' in pdf_py
    ), (
        "core/report_pdf.py não contém mais um laço reconhecível para as Dicas Valiosas. "
        "Revise o contrato do PDF antes de remover esse bloco."
    )
