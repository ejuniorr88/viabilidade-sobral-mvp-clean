from __future__ import annotations

import json
from typing import Any, Dict, Optional
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

import streamlit as st
from supabase import Client, create_client

from core.env_secrets import get_secret, get_secret_str


AUTH_STATE_KEYS = [
    "auth_logged_in",
    "auth_user_id",
    "auth_user_email",
    "auth_user_name",
    "auth_message",
    "auth_last_error",
    "oauth_url",
    "last_oauth_code",
    "auth_sync_done",
]

_VERIFY_TIMEOUT_SECONDS = 8


def get_supabase_auth_client() -> Client:
    client = st.session_state.get("_supabase_auth_client")
    if client is None:
        client = create_client(
            get_secret_str("SUPABASE_URL", required=True),
            get_secret("SUPABASE_SERVICE_ROLE_KEY")
            if get_secret("SUPABASE_SERVICE_ROLE_KEY")
            else get_secret_str("SUPABASE_ANON_KEY", required=True),
        )
        st.session_state["_supabase_auth_client"] = client
    return client


def get_app_url() -> str:
    raw = get_secret_str("REDIRECT_URL", get_secret_str("APP_URL", "http://localhost:8501")).strip()
    if not raw:
        raw = "http://localhost:8501"

    parsed = urlparse(raw)
    if not parsed.scheme or not parsed.netloc:
        return "http://localhost:8501"

    return raw.rstrip("/")


def get_external_login_url() -> str:
    raw = get_secret_str("EXTERNAL_LOGIN_URL", "https://viabilidade-sobral-mvp-clean.vercel.app").strip()
    return raw.rstrip("/") or "https://viabilidade-sobral-mvp-clean.vercel.app"


def get_gateway_url() -> str:
    raw = get_secret_str("AUTH_GATEWAY_URL", "https://viabilidade-auth-gateway.onrender.com").strip()
    return raw.rstrip("/") or "https://viabilidade-auth-gateway.onrender.com"


def build_auth_callback_url() -> str:
    return get_app_url()


def safe_get_query_param(name: str) -> Optional[str]:
    try:
        value = st.query_params.get(name)
        if isinstance(value, list):
            return value[0] if value else None
        return value
    except Exception:
        try:
            params = st.experimental_get_query_params()
            values = params.get(name)
            if not values:
                return None
            return values[0]
        except Exception:
            return None


def clear_auth_query_params(remove_external_token: bool = False) -> None:
    keys = [
        "code",
        "state",
        "error",
        "error_code",
        "error_description",
        "auth_flow",
    ]
    if remove_external_token:
        keys.append("ext_access_token")

    try:
        for key in keys:
            try:
                del st.query_params[key]
            except Exception:
                pass
    except Exception:
        try:
            current = st.experimental_get_query_params()
            cleaned = {k: v for k, v in current.items() if k not in keys}
            st.experimental_set_query_params(**cleaned)
        except Exception:
            pass


def extract_user_fields(user_obj: Any) -> Dict[str, Optional[str]]:
    if user_obj is None:
        return {"id": None, "email": None, "name": None}

    if isinstance(user_obj, dict):
        meta = user_obj.get("user_metadata") or {}
        return {
            "id": user_obj.get("id"),
            "email": user_obj.get("email"),
            "name": user_obj.get("name") or meta.get("full_name") or meta.get("name"),
        }

    meta = getattr(user_obj, "user_metadata", None) or {}
    if not isinstance(meta, dict):
        meta = {}

    return {
        "id": getattr(user_obj, "id", None),
        "email": getattr(user_obj, "email", None),
        "name": meta.get("full_name") or meta.get("name"),
    }


def store_user_in_state(user_obj: Any) -> None:
    info = extract_user_fields(user_obj)
    st.session_state["auth_logged_in"] = bool(info["id"] or info["email"])
    st.session_state["auth_user_id"] = info["id"]
    st.session_state["auth_user_email"] = info["email"]
    st.session_state["auth_user_name"] = info["name"]
    st.session_state["auth_sync_done"] = True


def clear_user_in_state() -> None:
    st.session_state["auth_logged_in"] = False
    st.session_state["auth_user_id"] = None
    st.session_state["auth_user_email"] = None
    st.session_state["auth_user_name"] = None
    st.session_state["auth_sync_done"] = True


def _verify_external_access_token(access_token: str) -> Dict[str, Any]:
    payload = json.dumps({"access_token": access_token}).encode("utf-8")
    req = Request(
        f"{get_gateway_url()}/api/auth/session/verify",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(req, timeout=_VERIFY_TIMEOUT_SECONDS) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else {}


def _get_external_token() -> Optional[str]:
    return st.session_state.get("auth_external_access_token") or safe_get_query_param("ext_access_token")


def _try_restore_from_external_token(force_verify: bool = False) -> bool:
    token = _get_external_token()
    if not token:
        return False

    cached_token = st.session_state.get("auth_external_access_token")
    has_user = bool(st.session_state.get("auth_user_id") and st.session_state.get("auth_logged_in"))

    if not force_verify and has_user and cached_token == token:
        st.session_state["auth_sync_done"] = True
        return True

    verified = _verify_external_access_token(token)
    user_obj = verified.get("user") or {}
    if not user_obj:
        raise RuntimeError("Usuário não retornado pelo gateway.")

    store_user_in_state(user_obj)
    st.session_state["auth_external_access_token"] = token
    st.session_state.pop("auth_last_error", None)
    return True


def sync_auth_state(force: bool = False) -> bool:
    if st.session_state.get("auth_sync_done") and not force:
        return bool(st.session_state.get("auth_logged_in"))

    try:
        restored = _try_restore_from_external_token(force_verify=force)
        st.session_state["auth_sync_done"] = True
        return restored
    except Exception as e:
        clear_user_in_state()
        st.session_state["auth_last_error"] = f"Falha ao restaurar login: {e}"
        return False


def handle_oauth_callback() -> None:
    error = safe_get_query_param("error")
    error_description = safe_get_query_param("error_description")
    external_access_token = safe_get_query_param("ext_access_token")

    if error:
        clear_user_in_state()
        st.session_state["auth_last_error"] = (
            f"Erro no login Google: {error}"
            + (f" — {error_description}" if error_description else "")
        )
        st.session_state.pop("oauth_url", None)
        clear_auth_query_params(remove_external_token=True)
        st.rerun()
        return

    if external_access_token:
        try:
            # Se já validamos este mesmo token nesta sessão, não chama o gateway de novo.
            if (
                st.session_state.get("auth_external_access_token") == external_access_token
                and st.session_state.get("auth_logged_in")
                and st.session_state.get("auth_user_id")
            ):
                st.session_state["auth_sync_done"] = True
                st.session_state.pop("auth_last_error", None)
                return

            _try_restore_from_external_token(force_verify=True)
            st.session_state["auth_message"] = "Login efetuado com sucesso."
            st.session_state.pop("oauth_url", None)
            # Mantém o ext_access_token para permitir reidratação no refresh.
            clear_auth_query_params(remove_external_token=False)
            st.rerun()
            return
        except Exception as e:
            clear_user_in_state()
            st.session_state["auth_last_error"] = f"Falha ao concluir login: {e}"
            st.session_state.pop("oauth_url", None)
            # Se o token falhar, limpamos para evitar travar em estado intermediário.
            clear_auth_query_params(remove_external_token=True)
            st.rerun()
            return

    sync_auth_state(force=False)


def get_auth_url(force_select_account: bool = False) -> Optional[str]:
    base = get_external_login_url()
    params: Dict[str, Any] = {}
    if force_select_account:
        params["switch_account"] = "1"

    if params:
        return f"{base}?{urlencode(params)}"
    return base


def logout_limpo() -> None:
    keep = {
        "_supabase_auth_client": st.session_state.get("_supabase_auth_client"),
    }
    for k in AUTH_STATE_KEYS:
        st.session_state.pop(k, None)
    clear_user_in_state()
    st.session_state.pop("auth_external_access_token", None)
    st.session_state.pop("oauth_url", None)
    if keep.get("_supabase_auth_client") is not None:
        st.session_state["_supabase_auth_client"] = keep["_supabase_auth_client"]
    clear_auth_query_params(remove_external_token=True)
    st.rerun()


# Compat wrappers for existing ui/auth_panel.py
def start_google_login(force_select_account: bool = False) -> Optional[str]:
    return get_auth_url(force_select_account=force_select_account)


def sign_out_current_user() -> None:
    logout_limpo()
