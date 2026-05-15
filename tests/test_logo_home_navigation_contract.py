from pathlib import Path


def test_logo_home_query_param_is_consumed_before_special_pages() -> None:
    text = Path("app.py").read_text(encoding="utf-8")

    assert 'consume_home_nav_query_param(st.session_state)' in text
    assert 'if st.session_state.get("show_plans_page"):' in text
    assert 'if st.session_state.get("show_client_area"):' in text

    consume_pos = text.index('consume_home_nav_query_param(st.session_state)')
    plans_pos = text.index('if st.session_state.get("show_plans_page"):')
    client_pos = text.index('if st.session_state.get("show_client_area"):')

    assert consume_pos < plans_pos
    assert consume_pos < client_pos


def test_home_nav_query_param_clears_special_page_state() -> None:
    text = Path("ui/runtime/app_query_params.py").read_text(encoding="utf-8")

    required = [
        'session_state["show_plans_page"] = False',
        'session_state["show_client_area"] = False',
        'session_state["post_login_action"] = None',
        'clear_all_checkout_states()',
        'clear_home_nav_query_param()',
    ]

    for item in required:
        assert item in text, f"Contrato de nav=home perdido: {item}"
