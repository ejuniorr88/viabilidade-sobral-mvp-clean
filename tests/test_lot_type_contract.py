from pathlib import Path


def _read(path: str) -> str:
    root = Path(__file__).resolve().parents[1]
    return (root / path).read_text(encoding="utf-8")


def test_lot_type_ui_contract():
    content = _read("ui/lote.py")
    assert "Lote meio de quadra" in content
    assert "Lote de esquina" in content


def test_lot_type_figuras_contract():
    content = _read("ui/relatorio_blocks/figuras_anexo_v.py")
    assert "1" in content and "2" in content and "3" in content and "4" in content
    assert "5" in content and "6" in content and "7" in content


def test_dicas_valiosas_corner_has_extra_temp_text_contract():
    content = _read("ui/relatorio_blocks/dicas_valiosas.py")
    assert "def get_dicas_valiosas" in content

    accepted_variants = [
        "Texto temporário - lote de esquina",
        "Texto temporário – lote de esquina",
        "**Texto temporário - lote de esquina**",
        "**Texto temporário – lote de esquina**",
    ]
    assert any(v in content for v in accepted_variants), (
        "ui/relatorio_blocks/dicas_valiosas.py precisa conter um texto temporário "
        "específico para lote de esquina, aceitando hífen normal ou travessão."
    )
