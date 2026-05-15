from core.session.bootstrap import bootstrap_session_state


def test_bootstrap_session_state_initializes_required_defaults() -> None:
    session_state = {}

    bootstrap_session_state(session_state)

    assert session_state["calc"] == {}
    assert session_state["last_calc_signature"] is None
    assert session_state["confirm_new_report"] is False
    assert session_state["free_calc_done"] is False
    assert session_state["show_login_gate"] is False
    assert session_state["scroll_to_login_gate"] is False
    assert session_state["scroll_to_item3"] is False
    assert session_state["post_login_action"] is None
    assert session_state["show_inline_payments"] is False
    assert session_state["show_plans_page"] is False
    assert session_state["show_client_area"] is False


def test_bootstrap_session_state_preserves_existing_values() -> None:
    session_state = {
        "calc": {"ok": True},
        "last_calc_signature": "sig",
        "confirm_new_report": True,
        "free_calc_done": True,
        "show_login_gate": True,
        "show_plans_page": True,
    }

    bootstrap_session_state(session_state)

    assert session_state["calc"] == {"ok": True}
    assert session_state["last_calc_signature"] == "sig"
    assert session_state["confirm_new_report"] is True
    assert session_state["free_calc_done"] is True
    assert session_state["show_login_gate"] is True
    assert session_state["show_plans_page"] is True
