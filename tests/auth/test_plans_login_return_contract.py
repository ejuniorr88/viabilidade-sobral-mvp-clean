from __future__ import annotations

import sys
import types
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_auth_url_can_preserve_checkout_return_params(monkeypatch) -> None:
    streamlit_stub = types.SimpleNamespace(session_state={})
    supabase_stub = types.SimpleNamespace(Client=object, create_client=lambda *args, **kwargs: None)
    monkeypatch.setitem(sys.modules, "streamlit", streamlit_stub)
    monkeypatch.setitem(sys.modules, "supabase", supabase_stub)

    from core import auth

    monkeypatch.setattr(auth, "get_external_login_url", lambda: "https://login.example.com")
    monkeypatch.setattr(auth, "get_gateway_url", lambda: "https://gateway.example.com")
    monkeypatch.setattr(auth, "get_app_url", lambda: "https://app.example.com")
    monkeypatch.setattr(auth, "_normalized_env_url", lambda name, fallback="", required=False: "https://supabase.example.com" if name == "SUPABASE_URL" else fallback)
    monkeypatch.setattr(auth, "get_secret_str", lambda name, fallback="", required=False: "anon-key" if name == "SUPABASE_ANON_KEY" else fallback)

    login_url = auth.get_auth_url(return_query_params={"checkout": "1", "plan": "profissional"})
    params = parse_qs(urlparse(login_url).query)

    assert params["streamlit_app_url"] == ["https://app.example.com?checkout=1&plan=profissional"]
    assert params["env_key"] == ["https://supabase.example.com|https://login.example.com|https://app.example.com"]


def test_plans_login_box_builds_return_query_params_from_checkout_state() -> None:
    text = _read(ROOT / "ui" / "auth_panel.py")

    required = [
        "def _build_post_login_return_query_params(",
        'st.session_state.get("post_login_action") == "open_plans_page"',
        'st.session_state.get("landing_checkout_mode")',
        'params: Dict[str, Any] = {"checkout": "1"}',
        'params["plan"] = selected_plan',
        "return_query_params=_build_post_login_return_query_params(context)",
    ]
    for item in required:
        assert item in text, f"Login dos planos perdeu a proteção de retorno pós-login: {item}"
