from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTH_PANEL = ROOT / "ui" / "auth_panel.py"
COMPONENT_INIT = ROOT / "components" / "auth_popup_component" / "__init__.py"
COMPONENT_JS = ROOT / "components" / "auth_popup_component" / "frontend" / "main.js"
CORE_AUTH = ROOT / "core" / "auth.py"


def test_auth_panel_does_not_write_external_access_token_to_url() -> None:
    text = AUTH_PANEL.read_text(encoding="utf-8", errors="ignore")

    assert 'st.query_params["ext_access_token"] = token' not in text
    assert 'st.session_state["auth_external_access_token"] = token' in text
    assert 'st.session_state["auth_sync_done"] = False' in text


def test_popup_component_persists_token_for_refresh_and_can_clear_on_logout() -> None:
    init_text = COMPONENT_INIT.read_text(encoding="utf-8", errors="ignore")
    js_text = COMPONENT_JS.read_text(encoding="utf-8", errors="ignore")

    for item in [
        "restore_token: bool = True",
        "clear_browser_token: bool = False",
        "restore_token=bool(restore_token)",
        "clear_browser_token=bool(clear_browser_token)",
    ]:
        assert item in init_text

    for item in [
        'const PERSISTED_TOKEN_KEY = "vf_auth_streamlit_access_token";',
        "function persistTokenForRefresh(token) {",
        "function readPersistedToken() {",
        "function clearBrowserTokens() {",
        "currentArgs.clear_browser_token",
        "currentArgs.restore_token",
        "setComponentValue(persistedToken);",
    ]:
        assert item in js_text


def test_logout_requests_browser_token_cleanup_without_removing_functional_url_fallback() -> None:
    panel_text = AUTH_PANEL.read_text(encoding="utf-8", errors="ignore")
    auth_text = CORE_AUTH.read_text(encoding="utf-8", errors="ignore")

    assert 'st.session_state["auth_clear_browser_token"] = True' in panel_text
    assert 'st.session_state["auth_clear_browser_token"] = True' in auth_text
    # Mantém a versão funcional atual como fallback controlado; não reintroduz o patch v2 quebrado.
    assert "clear_auth_query_params(remove_external_token=False)" in auth_text
