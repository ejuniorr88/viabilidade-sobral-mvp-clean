from pathlib import Path

APP_PY = Path(__file__).resolve().parents[2] / 'app.py'
AUTH_PY = Path(__file__).resolve().parents[2] / 'core' / 'auth.py'
AUTH_PANEL_PY = Path(__file__).resolve().parents[2] / 'ui' / 'auth_panel.py'


def _read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def test_app_reads_persisted_auth_session_keys():
    text = _read(APP_PY)
    assert 'user_logged_in = bool(st.session_state.get("auth_logged_in"))' in text
    assert 'user_id = st.session_state.get("auth_user_id")' in text
    assert 'user_email = st.session_state.get("auth_user_email")' in text


def test_core_auth_exports_and_sets_canonical_session_keys():
    text = _read(AUTH_PY)
    for key in ('auth_logged_in', 'auth_user_id', 'auth_user_email'):
        assert f'"{key}"' in text
    assert 'st.session_state["auth_logged_in"] = bool(info["id"] or info["email"])' in text
    assert 'st.session_state["auth_user_id"] = info["id"]' in text
    assert 'st.session_state["auth_user_email"] = info["email"]' in text


def test_auth_panel_depends_on_same_session_keys():
    text = _read(AUTH_PANEL_PY)
    assert 'st.session_state.get("auth_logged_in")' in text
    assert 'st.session_state.get("auth_user_id")' in text
    assert 'st.session_state.get("auth_user_email")' in text
