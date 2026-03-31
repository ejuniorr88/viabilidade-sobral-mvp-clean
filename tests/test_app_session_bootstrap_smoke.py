from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_app_bootstrap_initializes_minimum_session_state_before_calc_usage() -> None:
    text = (ROOT / "app.py").read_text(encoding="utf-8")

    helper = "def _ensure_minimum_session_state() -> None:"
    calc_init = 'st.session_state.calc = {}'
    call = '_ensure_minimum_session_state()'
    first_calc_use = 'st.session_state.calc["use_type_code"] = selected_use_code'

    assert helper in text, "app.py perdeu o helper mínimo de bootstrap do session_state."
    assert calc_init in text, "app.py não garante calc como dict no boot."
    assert call in text, "app.py não chama o bootstrap mínimo do session_state no boot."
    assert first_calc_use in text, "Âncora de uso de calc mudou; revise o teste."

    assert text.index(call) < text.index(first_calc_use), (
        "app.py usa st.session_state.calc antes de garantir o bootstrap mínimo do session_state."
    )


def test_app_bootstrap_keeps_basic_runtime_defaults() -> None:
    text = (ROOT / "app.py").read_text(encoding="utf-8")
    required = [
        'st.session_state.free_calc_done = False',
        'st.session_state.show_login_gate = False',
        'st.session_state.scroll_to_login_gate = False',
        'st.session_state.scroll_to_item3 = False',
        'st.session_state.post_login_action = None',
        'st.session_state.show_inline_payments = False',
    ]
    for item in required:
        assert item in text, f"Bootstrap mínimo do session_state perdeu default crítico: {item}"
