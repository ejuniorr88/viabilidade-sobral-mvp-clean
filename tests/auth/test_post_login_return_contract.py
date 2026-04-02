from pathlib import Path

APP_PY = Path(__file__).resolve().parents[2] / 'app.py'
ACCESS_GATES_PY = Path(__file__).resolve().parents[2] / 'ui' / 'access_gates.py'
RUNTIME_FLOW_PY = Path(__file__).resolve().parents[2] / 'ui' / 'runtime' / 'flow_state.py'


def _read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def test_app_delegates_post_login_runtime_flags():
    text = _read(APP_PY)
    assert 'from ui.runtime.flow_state import apply_post_login_runtime_flags, render_item3_scroll_if_needed' in text
    assert 'apply_post_login_runtime_flags(' in text
    assert 'user_logged_in=user_logged_in' in text
    assert 'user_id=user_id' in text


def test_calculate_viability_post_login_action_is_preserved():
    text = _read(ACCESS_GATES_PY)
    assert 'session_state["post_login_action"] = "calculate_viability"' in text
    assert 'session_state.get("post_login_action") == "calculate_viability"' in text
    assert 'session_state["post_login_action"] = None' in text


def test_open_client_area_post_login_action_is_handled_only_in_runtime_module():
    text = _read(RUNTIME_FLOW_PY)
    assert 'open_client_area' in text
    assert 'calculate_viability' not in text
