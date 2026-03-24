from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='ignore')


def test_login_flow_contract_keeps_google_login_entrypoints() -> None:
    auth_panel = _read(ROOT / 'ui' / 'auth_panel.py')
    app_py = _read(ROOT / 'app.py')

    required = [
        'Entrar com Google',
        'render_google_login_box',
        'render_google_login_top',
        'Faça login para continuar',
    ]
    haystack = auth_panel + '\n' + app_py
    for item in required:
        assert item in haystack, f"Fluxo de login perdeu a âncora crítica: {item}"


def test_login_flow_contract_keeps_client_area_post_login_handoff() -> None:
    app_py = _read(ROOT / 'app.py')

    required = [
        'Área do cliente',
        'key="vf_nav_client"',
        'st.session_state["show_client_area"] = True',
        'st.session_state["post_login_action"] = "open_client_area"',
        'st.session_state.get("post_login_action") == "open_client_area"',
        'render_client_area_page(',
        'st.rerun()',
    ]
    for item in required:
        assert item in app_py, (
            'Fluxo crítico da Área do cliente após login foi alterado ou removido: '
            f'{item}'
        )


def test_login_flow_contract_keeps_session_and_logout_anchors() -> None:
    auth_py = _read(ROOT / 'core' / 'auth.py')
    app_py = _read(ROOT / 'app.py')

    required_auth = [
        'sync_auth_state',
        'store_user_in_state',
        'clear_user_in_state',
        'logout_limpo',
        'auth_logged_in',
        'auth_user_id',
        'auth_user_email',
        'auth_user_name',
    ]
    for item in required_auth:
        assert item in auth_py, f"Âncora crítica de sessão/login foi removida: {item}"

    assert 'logout_limpo(' in auth_py, 'Logout limpo precisa continuar existindo no core/auth.py.'
    assert 'auth_logged_in' in app_py, 'app.py precisa continuar verificando auth_logged_in para proteger fluxos.'
