from pathlib import Path

APP_PY = Path(__file__).resolve().parents[2] / 'app.py'
APP_SHELL_PY = Path(__file__).resolve().parents[2] / 'ui' / 'app_shell.py'
RUNTIME_FLOW_PY = Path(__file__).resolve().parents[2] / 'ui' / 'runtime' / 'flow_state.py'


def _read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def test_top_nav_sets_open_client_area_post_login_path():
    text = _read(APP_SHELL_PY)
    assert 'st.session_state["show_client_area"] = True' in text
    assert 'if not st.session_state.get("auth_logged_in"):' in text
    assert 'st.session_state["post_login_action"] = "open_client_area"' in text


def test_runtime_flow_opens_client_area_after_login():
    text = _read(RUNTIME_FLOW_PY)
    assert 'session_state.get("post_login_action") == "open_client_area"' in text
    assert 'session_state["show_client_area"] = True' in text
    assert 'session_state["post_login_action"] = None' in text


def test_app_uses_client_area_gate_and_stops_after_render():
    text = _read(APP_PY)
    assert 'render_client_area_gate(' in text
    assert 'if st.session_state.get("show_client_area"):' in text
    assert 'st.stop()' in text
