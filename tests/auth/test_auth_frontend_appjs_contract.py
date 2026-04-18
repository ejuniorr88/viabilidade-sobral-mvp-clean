from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_JS = ROOT / 'auth_external' / 'auth_frontend' / 'app.js'


def _read() -> str:
    return APP_JS.read_text(encoding='utf-8')


def test_auth_frontend_appjs_keeps_runtime_only_configuration_contract() -> None:
    text = _read()

    required = [
        'SUPABASE_URL: normalizeUrl(',
        'getQueryParam("supabase_url") ||',
        'readStorage(STORAGE_KEYS.supabaseUrl) ||',
        'baseCfg.SUPABASE_URL',
        'SUPABASE_ANON_KEY: (',
        'getQueryParam("supabase_anon_key") ||',
        'readStorage(STORAGE_KEYS.supabaseAnonKey) ||',
        'baseCfg.SUPABASE_ANON_KEY',
        'GATEWAY_BASE_URL: normalizeUrl(',
        'getQueryParam("gateway_base_url") ||',
        'readStorage(STORAGE_KEYS.gatewayBaseUrl) ||',
        'baseCfg.GATEWAY_BASE_URL',
        'LOGIN_REDIRECT_URL: normalizeUrl(',
        'getQueryParam("login_redirect_url") ||',
        'readStorage(STORAGE_KEYS.loginRedirectUrl) ||',
        'baseCfg.LOGIN_REDIRECT_URL',
        'STREAMLIT_APP_URL: normalizeUrl(',
        'getQueryParam("streamlit_app_url") ||',
        'readStorage(STORAGE_KEYS.preferredAppUrl) ||',
        'baseCfg.STREAMLIT_APP_URL',
        'persistRuntimeConfig(cfg);',
    ]
    for item in required:
        assert item in text, f'Blindagem da config dinâmica do login perdeu a âncora: {item}'



def test_auth_frontend_appjs_keeps_oauth_callback_params_contract() -> None:
    text = _read()

    required = [
        'callbackUrl.searchParams.set("streamlit_app_url", preferredAppUrl);',
        'callbackUrl.searchParams.set("gateway_base_url", runtimeCfg.GATEWAY_BASE_URL);',
        'callbackUrl.searchParams.set("supabase_url", runtimeCfg.SUPABASE_URL);',
        'callbackUrl.searchParams.set("supabase_anon_key", runtimeCfg.SUPABASE_ANON_KEY);',
        'const switchAccount = getQueryParam("switch_account");',
        'callbackUrl.searchParams.set("switch_account", switchAccount);',
        'prompt: "select_account"',
    ]
    for item in required:
        assert item in text, f'Callback do Google perdeu parâmetro crítico: {item}'



def test_auth_frontend_appjs_keeps_popup_handoff_and_race_guards_contract() -> None:
    text = _read()

    required = [
        'let refreshStatePromise = null;',
        'let suppressAuthStateRefresh = false;',
        'if (refreshStatePromise) {',
        'if (isPopupFlow() && hasOAuthCallbackHash()) {',
        'window.opener.postMessage({ type: "vf_auth_success", access_token: accessToken }, "*");',
        'const channel = new BroadcastChannel("vf-auth-popup");',
        'channel.postMessage({ type: "vf_auth_success", access_token: accessToken });',
        'writeStorage(STORAGE_KEYS.popupToken, accessToken);',
        'if (suppressAuthStateRefresh) return;',
        'await refreshState();',
    ]
    for item in required:
        assert item in text, f'Blindagem do handoff popup->app perdeu a âncora: {item}'



def test_auth_frontend_appjs_does_not_reintroduce_slow_or_aggressive_regressions() -> None:
    text = _read()
    forbidden = [
        'wakeGateway(',
        'window.opener.location.href',
        'localhost:3000',
        '127.0.0.1',
    ]
    for item in forbidden:
        assert item not in text, f'Login externo reintroduziu regressão proibida: {item}'
