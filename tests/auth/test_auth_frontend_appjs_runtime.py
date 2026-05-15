from __future__ import annotations

import json
import subprocess
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_JS = ROOT / 'auth_external' / 'auth_frontend' / 'app.js'


def _run_node_scenario(scenario: str) -> dict:
    app_js = APP_JS.read_text(encoding='utf-8')
    script = f"""
const APP_JS_SOURCE = {json.dumps(app_js)};

function createStorage() {{
  const store = new Map();
  return {{
    getItem(key) {{ return store.has(key) ? store.get(key) : null; }},
    setItem(key, value) {{ store.set(String(key), String(value)); }},
    removeItem(key) {{ store.delete(key); }},
    dump() {{ return Object.fromEntries(store.entries()); }},
  }};
}}

function createElement(id) {{
  return {{
    id,
    hidden: false,
    disabled: false,
    className: '',
    textContent: '',
    listeners: {{}},
    addEventListener(type, cb) {{ this.listeners[type] = cb; }},
    async click() {{ if (this.listeners.click) return await this.listeners.click({{}}); }},
  }};
}}

async function main() {{
  const outputs = {{ fetchCalls: [], postMessages: [], broadcasts: [], historyReplaced: 0 }};
  const elements = {{
    loginBtn: createElement('loginBtn'),
    logoutBtn: createElement('logoutBtn'),
    continueBtn: createElement('continueBtn'),
    status: createElement('status'),
  }};
  const sessionStorage = createStorage();
  const localStorage = createStorage();
  const opener = {{
    location: {{ href: 'https://app.example.com/original' }},
    postMessage(payload, target) {{ outputs.postMessages.push({{ payload, target }}); }},
  }};

  const windowObj = {{
    AUTH_CONFIG: {{}},
    sessionStorage,
    localStorage,
    location: {{
      search: '',
      hash: '',
      origin: 'https://login.example.com',
      pathname: '/index.html',
      href: 'https://login.example.com/index.html',
    }},
    name: '',
    opener: null,
    setTimeout,
    clearTimeout,
    close() {{ outputs.closed = true; }},
  }};

  const historyObj = {{
    replaceState(_a, _b, nextUrl) {{
      outputs.historyReplaced += 1;
      outputs.historyUrl = nextUrl;
      windowObj.location.hash = '';
    }},
  }};

  global.window = windowObj;
  global.document = {{ getElementById(id) {{ return elements[id] || null; }} }};
  global.history = historyObj;
  global.BroadcastChannel = class BroadcastChannel {{
    constructor(name) {{ this.name = name; }}
    postMessage(payload) {{ outputs.broadcasts.push({{ name: this.name, payload }}); }}
    close() {{}}
  }};
  global.fetch = async function(url, _options) {{
    outputs.fetchCalls.push(String(url));
    return {{ ok: true, json: async () => ({{ user: {{ email: 'user@example.com' }} }}), text: async () => '' }};
  }};

  const authStateListeners = [];
  let getSessionCalls = 0;
  let signOutCalls = 0;
  let signInPayload = null;
  global.window.supabase = {{
    createClient(supabaseUrl, anonKey) {{
      outputs.createdClient = {{ supabaseUrl, anonKey }};
      return {{
        auth: {{
          async getSession() {{
            getSessionCalls += 1;
            if ({json.dumps(scenario)} === 'popup_callback') {{
              return {{ data: {{ session: {{ access_token: 'tok_popup', user: {{ email: 'popup@example.com' }} }} }}, error: null }};
            }}
            if ({json.dumps(scenario)} === 'continue_main') {{
              return {{ data: {{ session: {{ access_token: 'tok_continue', user: {{ email: 'main@example.com' }} }} }}, error: null }};
            }}
            return {{ data: {{ session: {{ access_token: 'tok_login', user: {{ email: 'login@example.com' }} }} }}, error: null }};
          }},
          async signInWithOAuth(payload) {{ signInPayload = payload; return {{ error: null }}; }},
          async signOut() {{ signOutCalls += 1; return {{ error: null }}; }},
          onAuthStateChange(cb) {{ authStateListeners.push(cb); return {{ data: {{ subscription: {{ unsubscribe() {{}} }} }} }}; }},
        }},
      }};
    }},
  }};
  global.supabase = global.window.supabase;

  if ({json.dumps(scenario)} === 'popup_callback') {{
    windowObj.name = 'vfGoogleLoginPopup';
    windowObj.opener = opener;
    windowObj.location.search = '?streamlit_app_url=https%3A%2F%2Fapp.example.com&gateway_base_url=https%3A%2F%2Fgateway.example.com&supabase_url=https%3A%2F%2Fsupabase.example.com&supabase_anon_key=anon123';
    windowObj.location.hash = '#access_token=fakehash';
  }} else if ({json.dumps(scenario)} === 'login_click') {{
    windowObj.location.search = '?streamlit_app_url=https%3A%2F%2Fapp.example.com%2Fclient&gateway_base_url=https%3A%2F%2Fgateway.example.com&supabase_url=https%3A%2F%2Fsupabase.example.com&supabase_anon_key=anonXYZ&login_redirect_url=https%3A%2F%2Flogin.example.com%2Findex.html&switch_account=1';
  }} else if ({json.dumps(scenario)} === 'logout_cleanup') {{
    windowObj.location.search = '?streamlit_app_url=https%3A%2F%2Fapp.example.com&gateway_base_url=https%3A%2F%2Fgateway.example.com&supabase_url=https%3A%2F%2Fsupabase.example.com&supabase_anon_key=anonXYZ';
    sessionStorage.setItem('vf_access_token', 'tok_old');
    sessionStorage.setItem('vf_user', '{{"email":"old@example.com"}}');
    sessionStorage.setItem('vf_auth_popup_token', 'tok_popup_old');
    localStorage.setItem('vf_access_token', 'tok_old');
    localStorage.setItem('vf_user', '{{"email":"old@example.com"}}');
    localStorage.setItem('vf_auth_popup_token', 'tok_popup_old');
  }}

  eval(APP_JS_SOURCE);

  if ({json.dumps(scenario)} === 'login_click') {{
    await new Promise((resolve) => setTimeout(resolve, 20));
    await elements.loginBtn.click();
    await new Promise((resolve) => setTimeout(resolve, 20));
  }} else if ({json.dumps(scenario)} === 'logout_cleanup') {{
    await new Promise((resolve) => setTimeout(resolve, 20));
    await elements.logoutBtn.click();
    await new Promise((resolve) => setTimeout(resolve, 20));
  }} else {{
    await new Promise((resolve) => setTimeout(resolve, 260));
  }}

  outputs.signInPayload = signInPayload;
  outputs.getSessionCalls = getSessionCalls;
  outputs.signOutCalls = signOutCalls;
  outputs.statusText = elements.status.textContent;
  outputs.statusClass = elements.status.className;
  outputs.loginHidden = elements.loginBtn.hidden;
  outputs.logoutHidden = elements.logoutBtn.hidden;
  outputs.continueHidden = elements.continueBtn.hidden;
  outputs.sessionStorage = sessionStorage.dump();
  outputs.localStorage = localStorage.dump();
  outputs.openerHref = opener.location.href;
  console.log(JSON.stringify(outputs));
}}

main().catch((err) => {{
  console.error(err);
  process.exit(1);
}});
"""
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as tmp:
        tmp.write(textwrap.dedent(script))
        temp_path = Path(tmp.name)
    try:
        result = subprocess.run(
            ['node', str(temp_path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout.strip())
    finally:
        temp_path.unlink(missing_ok=True)



def test_auth_frontend_popup_callback_handoff_is_fast_and_does_not_hit_gateway() -> None:
    result = _run_node_scenario('popup_callback')

    assert result['fetchCalls'] == [], 'Popup no retorno do Google não deve bater no gateway antes de devolver o token.'
    assert result['postMessages'] == [
        {'payload': {'type': 'vf_auth_success', 'access_token': 'tok_popup'}, 'target': 'https://app.example.com'}
    ]
    assert result['broadcasts'] == [
        {'name': 'vf-auth-popup', 'payload': {'type': 'vf_auth_success', 'access_token': 'tok_popup'}}
    ]
    assert result['sessionStorage']['vf_auth_popup_token'] == 'tok_popup'
    assert result['localStorage']['vf_auth_popup_token'] == 'tok_popup'
    assert result['openerHref'] == 'https://app.example.com/original'
    assert result['closed'] is True
    assert result['historyReplaced'] >= 1
    assert result['statusText'] == 'Login concluído. Voltando para o sistema...'
    assert result['statusClass'] == 'status ok'
    assert result['loginHidden'] is True
    assert result['logoutHidden'] is False
    assert result['continueHidden'] is False



def test_auth_frontend_login_click_builds_dynamic_redirect_without_hardcode() -> None:
    result = _run_node_scenario('login_click')

    payload = result['signInPayload']
    assert payload is not None, 'Clique de login precisa continuar chamando signInWithOAuth.'
    assert result['fetchCalls'] == ['https://gateway.example.com/api/auth/session/verify'], (
        'Fluxo principal pode validar sessão existente, mas não deve aquecer gateway antes do clique.'
    )
    assert payload['provider'] == 'google'
    redirect_to = payload['options']['redirectTo']
    assert 'streamlit_app_url=https%3A%2F%2Fapp.example.com%2Fclient' in redirect_to
    assert 'gateway_base_url=https%3A%2F%2Fgateway.example.com' in redirect_to
    assert 'supabase_url=https%3A%2F%2Fsupabase.example.com' in redirect_to
    assert 'supabase_anon_key=anonXYZ' in redirect_to
    assert 'switch_account=1' in redirect_to
    assert payload['options']['queryParams']['prompt'] == 'select_account'
    assert result['statusText'] == 'Redirecionando para o Google...'
    assert result['sessionStorage']['vf_auth_supabase_anon_key'] == 'anonXYZ'
    assert result['localStorage']['vf_auth_supabase_anon_key'] == 'anonXYZ'



def test_auth_frontend_logout_clears_popup_and_session_storage_contract() -> None:
    result = _run_node_scenario('logout_cleanup')

    assert result['signOutCalls'] == 1
    assert 'vf_access_token' not in result['sessionStorage']
    assert 'vf_user' not in result['sessionStorage']
    assert 'vf_auth_popup_token' not in result['sessionStorage']
    assert 'vf_access_token' not in result['localStorage']
    assert 'vf_user' not in result['localStorage']
    assert 'vf_auth_popup_token' not in result['localStorage']
    assert result['statusText'] == 'Sessão encerrada.'
    assert result['statusClass'] == 'status muted'
    assert result['loginHidden'] is False
    assert result['logoutHidden'] is True
    assert result['continueHidden'] is True
