from pathlib import Path


def test_app_bootstrap_initializes_session_state_before_use() -> None:
    text = Path("app.py").read_text(encoding="utf-8")

    required_defaults = [
        'if "calc" not in ss or not isinstance(ss.get("calc"), dict):',
        'ss["calc"] = {}',
        'ss.setdefault("last_calc_signature", None)',
        'ss.setdefault("confirm_new_report", False)',
        'ss.setdefault("free_calc_done", False)',
        'ss.setdefault("show_login_gate", False)',
        'ss.setdefault("scroll_to_login_gate", False)',
        'ss.setdefault("scroll_to_item3", False)',
        'ss.setdefault("post_login_action", None)',
        'ss.setdefault("show_inline_payments", False)',
        'ss.setdefault("show_client_area", False)',
    ]

    for item in required_defaults:
        assert item in text, f"Bootstrap do session_state perdeu item obrigatório: {item}"

    bootstrap_pos = text.index('_bootstrap_session_state()')
    first_calc_use_pos = text.index('st.session_state.calc["use_type_code"] = selected_use_code')
    first_signature_use_pos = text.index('if st.session_state.last_calc_signature and st.session_state.last_calc_signature != current_signature:')

    assert bootstrap_pos < first_calc_use_pos
    assert bootstrap_pos < first_signature_use_pos


def test_app_imports_card_helper_from_app_shell() -> None:
    text = Path("app.py").read_text(encoding="utf-8")
    assert 'from ui.app_shell import (' in text
    assert 'card as _card' in text
