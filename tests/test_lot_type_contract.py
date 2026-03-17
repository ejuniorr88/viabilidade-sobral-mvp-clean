from pathlib import Path


def _read(rel_path: str) -> str:
    return (Path(__file__).resolve().parents[1] / rel_path).read_text(encoding='utf-8')


def test_dicas_valiosas_corner_has_extra_temp_text_contract():
    content = _read('ui/relatorio_blocks/dicas_valiosas.py')
    assert 'def get_dicas_valiosas' in content
    assert 'Texto temporário — lote de esquina' in content
    assert 'Texto a ser escrito.' in content


def test_figuras_filter_meio_vs_esquina_contract():
    content = _read('ui/relatorio_blocks/figuras_anexo_v.py')
    assert 'def filter_figuras_by_lot_type' in content
    assert '{5, 6, 7} if is_corner else {1, 2, 3, 4}' in content


def test_lote_ui_has_midblock_checkbox_contract():
    content = _read('ui/lote.py')
    assert 'Lote meio de quadra' in content
    assert 'lot_is_midblock' in content
    assert 'lot_midblock_checkbox' in content
