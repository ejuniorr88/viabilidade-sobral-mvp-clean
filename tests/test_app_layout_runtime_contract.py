from pathlib import Path


def test_app_restores_login_top_and_map_order_contract():
    app_text = Path("app.py").read_text(encoding="utf-8")
    flow_text = Path("ui/flow/primary_actions.py").read_text(encoding="utf-8")

    assert "render_google_login_top()" in app_text
    map_import_idx = app_text.index("from ui.map.section import render_mapa_section")
    map_render_idx = app_text.index("radius_m = render_mapa_section(zones_gj)")
    button_idx = flow_text.index('"🚀 GERAR CONSULTA AOS ÍNDICES URBANÍSTICOS"')

    assert map_import_idx < map_render_idx
    assert "clicked_calcular = render_primary_actions(" in app_text
    assert button_idx >= 0


def test_app_bootstrap_session_state_exists_before_first_calc_use():
    text = Path("app.py").read_text(encoding="utf-8")
    form_text = Path("ui/consultation_form.py").read_text(encoding="utf-8")

    bootstrap_idx = text.index("bootstrap_session_state(st.session_state)")
    first_form_call_idx = text.index("render_consultation_form(st.session_state)")
    assert bootstrap_idx < first_form_call_idx

    assert 'session_state.calc["use_type_code"] = selected_use_code' in form_text
