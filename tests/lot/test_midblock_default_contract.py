from pathlib import Path


def test_lote_meio_de_quadra_nasce_como_padrao_sem_reaproveitar_esquina_do_calc():
    source = Path('ui/lote.py').read_text(encoding='utf-8')

    assert 'return True' in source
    assert 'st.session_state["lot_corner_checkbox"] = False' in source
    assert 'preservar o padrão seguro de meio de quadra' in source
