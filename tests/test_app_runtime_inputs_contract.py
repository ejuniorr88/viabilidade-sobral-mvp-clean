from pathlib import Path


def test_app_py_restores_runtime_inputs_before_calc_signature() -> None:
    text = Path('app.py').read_text(encoding='utf-8')

    area_line = 'st.session_state.calc["lot_area_m2"] = float(lot_area)'
    categoria_line = 'categoria_label = st.selectbox('
    lote_line = 'lot_area, built_ground, permeable_area = render_lote_section()'
    mapa_line = 'radius_m = render_mapa_section(zones_gj)'
    signature_line = 'current_signature = report_confirmation_core.build_calc_signature('

    assert categoria_line in text, 'app.py perdeu a definição de categoria_label antes da assinatura de cálculo.'
    assert lote_line in text, 'app.py perdeu a coleta de lot_area/built_ground/permeable_area antes do uso runtime.'
    assert mapa_line in text, 'app.py perdeu a renderização do mapa que fornece radius_m ao fluxo de localização.'
    assert area_line in text, 'app.py perdeu a persistência de lot_area_m2 no calc.'
    assert signature_line in text, 'app.py perdeu a montagem da assinatura de cálculo.'

    assert text.index(categoria_line) < text.index(signature_line), (
        'categoria_label precisa ser definido antes de build_calc_signature().'
    )
    assert text.index(lote_line) < text.index(area_line), (
        'lot_area precisa vir de render_lote_section() antes de ser convertido em float.'
    )
    assert text.index(mapa_line) < text.index('render_localizacao_section(True, zones_prepared, radius_m)'), (
        'radius_m precisa ser definido antes do fluxo de localização.'
    )
