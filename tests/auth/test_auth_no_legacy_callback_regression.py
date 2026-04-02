from pathlib import Path

APP_PY = Path(__file__).resolve().parents[2] / 'app.py'
AUTH_PY = Path(__file__).resolve().parents[2] / 'core' / 'auth.py'


def _read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def test_app_keeps_bridge_then_oauth_callback_order():
    text = _read(APP_PY)
    bridge = 'render_auth_callback_bridge()'
    callback = 'handle_oauth_callback()'
    assert bridge in text
    assert callback in text
    assert text.index(bridge) < text.index(callback)


def test_app_uses_auth_flow_callback_query_param_guard():
    text = _read(APP_PY)
    assert 'if safe_get_query_param("auth_flow") == "callback":' in text


def test_core_auth_still_exposes_handle_oauth_callback_entrypoint():
    text = _read(AUTH_PY)
    assert 'def handle_oauth_callback() -> None:' in text


def test_no_pkce_callback_reintroduced_in_app():
    text = _read(APP_PY)
    lowered = text.lower()
    assert 'pkce' not in lowered
