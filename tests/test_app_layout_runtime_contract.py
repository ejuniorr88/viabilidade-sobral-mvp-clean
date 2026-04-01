from pathlib import Path


def test_app_restores_login_top_and_map_order_contract():
    text = Path("app.py").read_text(encoding="utf-8")

    assert "render_google_login_top()" in text
    map_title_idx = text.index("'<div class=\"vf-section-title\">📍 Selecione o lote no mapa:</div>'")
    map_render_idx = text.index("radius_m = render_mapa_section(zones_gj)")
    button_idx = text.index('"🚀 GERAR ESTUDO DE VIABILIDADE"')

    assert map_title_idx < map_render_idx < button_idx


def test_app_bootstrap_session_state_exists_before_first_calc_use():
    text = Path("app.py").read_text(encoding="utf-8")
    bootstrap_idx = text.index("bootstrap_session_state(st.session_state)")
    first_calc_use_idx = text.index('st.session_state.calc["use_type_code"] = selected_use_code')
    assert bootstrap_idx < first_calc_use_idx
