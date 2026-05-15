from pathlib import Path


def test_app_delegates_bootstrap_to_core_session_module() -> None:
    text = Path("app.py").read_text(encoding="utf-8")

    assert 'from core.session.bootstrap import bootstrap_session_state' in text
    assert 'bootstrap_session_state(st.session_state)' in text
    assert 'def _bootstrap_session_state()' not in text

    bootstrap_pos = text.index('bootstrap_session_state(st.session_state)')
    first_form_use_pos = text.index('render_consultation_form(st.session_state)')
    first_signature_use_pos = text.index('if st.session_state.last_calc_signature and st.session_state.last_calc_signature != current_signature:')

    assert bootstrap_pos < first_form_use_pos
    assert bootstrap_pos < first_signature_use_pos


def test_app_imports_card_helper_from_app_shell() -> None:
    text = Path("app.py").read_text(encoding="utf-8")
    assert 'from ui.app_shell import (' in text
    assert 'card as _card' in text


def test_core_session_bootstrap_keeps_required_defaults() -> None:
    text = Path("core/session/bootstrap.py").read_text(encoding="utf-8")

    required_defaults = [
        'if "calc" not in session_state or not isinstance(session_state.get("calc"), dict):',
        'session_state["calc"] = {}',
        'session_state.setdefault("last_calc_signature", None)',
        'session_state.setdefault("confirm_new_report", False)',
        'session_state.setdefault("free_calc_done", False)',
        'session_state.setdefault("show_login_gate", False)',
        'session_state.setdefault("scroll_to_login_gate", False)',
        'session_state.setdefault("scroll_to_item3", False)',
        'session_state.setdefault("post_login_action", None)',
        'session_state.setdefault("show_inline_payments", False)',
        'session_state.setdefault("show_plans_page", False)',
        'session_state.setdefault("show_client_area", False)',
    ]

    for item in required_defaults:
        assert item in text, f"Bootstrap do session_state perdeu item obrigatório: {item}"
