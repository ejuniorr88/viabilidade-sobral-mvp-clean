from pathlib import Path


def test_app_py_restores_runtime_inputs_before_calc_signature() -> None:
    text = Path('app.py').read_text(encoding='utf-8')

    area_line = 'st.session_state.calc["lot_area_m2"] = float(lot_area)'
    categoria_candidates = [
        'categoria_label, selected_use_label, selected_use_code, selected_multi_tipo = render_use_selector(st.session_state)',
        'categoria_label = st.selectbox(',
        '= render_consultation_form(st.session_state)',
    ]
    lote_candidates = [
        'lot_area, built_ground, permeable_area = render_lot_inputs()',
        'lot_area, built_ground, permeable_area = render_lote_section()',
        '= render_consultation_form(st.session_state)',
    ]
    mapa_line = 'radius_m = render_mapa_section(zones_gj)'
    signature_line = 'current_signature = report_confirmation_core.build_calc_signature('
    localizacao_line = 'render_localizacao_section(True, zones_prepared, radius_m)'

    categoria_line = next((line for line in categoria_candidates if line in text), None)
    assert categoria_line is not None, 'app.py perdeu a definição de categoria_label antes da assinatura de cálculo.'
    lote_line = next((line for line in lote_candidates if line in text), None)
    assert lote_line is not None, (
        'app.py perdeu a coleta de lot_area/built_ground/permeable_area antes do uso runtime.'
    )
    assert mapa_line in text, 'app.py perdeu a renderização do mapa que fornece radius_m ao fluxo de localização.'
    assert area_line in text, 'app.py perdeu a persistência de lot_area_m2 no calc.'
    assert signature_line in text, 'app.py perdeu a montagem da assinatura de cálculo.'
    assert localizacao_line in text, 'app.py perdeu o fluxo de localização dependente de radius_m.'

    assert text.index(categoria_line) < text.index(signature_line), (
        'categoria_label precisa ser definido antes de build_calc_signature().'
    )
    assert text.index(lote_line) < text.index(area_line), (
        'lot_area precisa vir do bloco do lote antes de ser convertido em float.'
    )
    assert text.index(mapa_line) < text.index(localizacao_line), (
        'radius_m precisa ser definido antes do fluxo de localização.'
    )
