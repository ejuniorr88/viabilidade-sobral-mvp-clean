from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='ignore')


def test_login_flow_contract_keeps_google_login_entrypoints() -> None:
    auth_panel = _read(ROOT / 'ui' / 'auth_panel.py')
    app_py = _read(ROOT / 'app.py')
    access_gates = _read(ROOT / 'ui' / 'access_gates.py')
    app_shell = _read(ROOT / 'ui' / 'app_shell.py')

    required = [
        'Entrar com Google',
        'render_google_login_box',
        'render_google_login_top',
        'Faça login para continuar',
    ]
    haystack = auth_panel + '\n' + app_py + '\n' + access_gates
    for item in required:
        assert item in haystack, f"Fluxo de login perdeu a âncora crítica: {item}"


def test_login_popup_architecture_contract_is_component_based() -> None:
    """Blindagem: o botão do login deve ser um componente bidirecional (não HTML inline frágil)."""
    auth_panel = _read(ROOT / 'ui' / 'auth_panel.py')
    component_init = _read(ROOT / 'components' / 'auth_popup_component' / '__init__.py')

    # O painel deve usar o componente (não links com unsafe_allow_html para popup)
    assert 'render_auth_popup_button' in auth_panel
    assert 'unsafe_allow_html=True' not in auth_panel
    assert 'st.markdown(' not in auth_panel

    # O token precisa voltar para o Python e virar ext_access_token
    assert 'st.query_params["ext_access_token"] = token' in auth_panel
    assert 'st.rerun()' in auth_panel

    # O componente precisa ser declarado e expor a função pública
    assert 'components.declare_component' in component_init
    assert 'auth_popup_component' in component_init
    assert 'def render_auth_popup_button' in component_init


def test_login_popup_component_frontend_contract_has_root_and_button() -> None:
    """Blindagem: o iframe do componente deve ter #root e o JS deve abrir popup no clique."""
    comp_index = _read(ROOT / 'components' / 'auth_popup_component' / 'frontend' / 'index.html')
    comp_js = _read(ROOT / 'components' / 'auth_popup_component' / 'frontend' / 'main.js')

    assert 'id="root"' in comp_index
    assert 'main.js' in comp_index

    # O clique deve acontecer dentro do componente e abrir popup diretamente
    assert 'window.open' in comp_js
    assert 'vfGoogleLoginPopup' in comp_js

    # Handshake do retorno
    assert 'vf_auth_success' in comp_js
    assert 'vf_auth_ack' in comp_js
    assert 'streamlit:setComponentValue' in comp_js


def test_login_popup_external_frontend_contract_waits_for_ack_before_close() -> None:
    """Blindagem: o popup externo só pode fechar após ACK, evitando regressão de fechamento cedo."""
    external_js = _read(ROOT / 'auth_external' / 'auth_frontend' / 'app.js')

    assert 'waitForParentAck' in external_js
    assert 'vf_auth_ack' in external_js
    assert 'vf_auth_success' in external_js
    assert 'window.opener.postMessage' in external_js

    # Evita regressão do comportamento antigo: fechar em isPopupFlow() sem callback real
    assert 'if (isPopupFlow() && hasOAuthCallbackHash())' in external_js
    assert 'if (isPopupFlow()) {\n        notifyParentLogin' not in external_js


def test_login_popup_external_ui_contract_has_professional_copy_and_no_json_box() -> None:
    """Blindagem: texto profissional e sem bloco JSON técnico no popup externo."""
    external_index = _read(ROOT / 'auth_external' / 'auth_frontend' / 'index.html')

    assert 'Faça login com sua conta Google para acessar os recursos da plataforma.' in external_index
    assert 'Após o login, aguarde alguns segundos enquanto a autenticação é concluída na plataforma.' in external_index
    assert 'id="userBox"' not in external_index


def test_login_flow_contract_keeps_client_area_post_login_handoff() -> None:
    app_py = _read(ROOT / 'app.py')
    access_gates = _read(ROOT / 'ui' / 'access_gates.py')
    app_shell = _read(ROOT / 'ui' / 'app_shell.py')

    required = [
        'Área do cliente',
        'key="vf_nav_client"',
        'st.session_state["show_client_area"] = True',
        'st.session_state["post_login_action"] = "open_client_area"',
        'st.session_state.get("post_login_action") == "open_client_area"',
        'render_client_area_page(',
        'st.rerun()',
    ]
    haystack = app_py + '\n' + access_gates + '\n' + app_shell
    for item in required:
        assert item in haystack, (
            'Fluxo crítico da Área do cliente após login foi alterado ou removido: '
            f'{item}'
        )


def test_login_flow_contract_keeps_session_and_logout_anchors() -> None:
    auth_py = _read(ROOT / 'core' / 'auth.py')
    app_py = _read(ROOT / 'app.py')
    access_gates = _read(ROOT / 'ui' / 'access_gates.py')

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
