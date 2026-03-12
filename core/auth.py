from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import urlparse

import streamlit as st
from supabase import Client, create_client

from core.supabase_client import get_supabase_config


AUTH_STATE_KEYS = [
    "auth_logged_in",
    "auth_user_id",
    "auth_user_email",
    "auth_user_name",
    "auth_sync_done",
    "last_oauth_code",
]

LOGOUT_CLEAN_KEYS = [
    "auth_logged_in",
    "auth_user_id",
    "auth_user_email",
    "auth_user_name",
    "auth_message",
    "auth_sync_done",
    "last_oauth_code",
    "post_login_action",
    "report_unlocked",
    "last_calc_signature",
    "show_inline_payments",
]


def get_supabase_auth_client() -> Client:
    client = st.session_state.get("_supabase_auth_client")
    if client is None:
        cfg = get_supabase_config()
        client = create_client(cfg.url, cfg.anon_key)
        st.session_state["_supabase_auth_client"] = client
    return client


def get_app_url() -> str:
    raw = str(st.secrets.get("APP_URL", "http://localhost:8501")).strip()
    if not raw:
        raw = "http://localhost:8501"

    parsed = urlparse(raw)
    if not parsed.scheme or not parsed.netloc:
        return "http://localhost:8501"

    return raw.rstrip("/")


def build_auth_callback_url() -> str:
    explicit = str(st.secrets.get("REDIRECT_URL", "")).strip()
    if explicit:
        parsed = urlparse(explicit)
        if parsed.scheme and parsed.netloc:
            return explicit.rstrip("/")
    return get_app_url()


def _as_single_query_value(value: Any) -> Optional[str]:
    if isinstance(value, list):
        return value[0] if value else None
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def safe_get_query_param(name: str) -> Optional[str]:
    try:
        return _as_single_query_value(st.query_params.get(name))
    except Exception:
        try:
            params = st.experimental_get_query_params()
            return _as_single_query_value(params.get(name))
        except Exception:
            return None


def clear_auth_query_params() -> None:
    keys = ["code", "state", "error", "error_code", "error_description", "auth_flow"]
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
            "name": meta.get("full_name") or meta.get("name"),
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


def _extract_user_from_auth_response(result: Any) -> Any:
    if result is None:
        return None

    user_obj = getattr(result, "user", None)
    if user_obj is not None:
        return user_obj

    if isinstance(result, dict):
        user_obj = result.get("user")
        if user_obj is not None:
            return user_obj
        session_obj = result.get("session")
    else:
        session_obj = getattr(result, "session", None)

    if session_obj is None:
        return None

    user_obj = getattr(session_obj, "user", None)
    if user_obj is not None:
        return user_obj
    if isinstance(session_obj, dict):
        return session_obj.get("user")
    return None


def sync_user_from_current_session(force: bool = False) -> bool:
    if st.session_state.get("auth_sync_done") and not force:
        return bool(st.session_state.get("auth_logged_in"))

    supabase = get_supabase_auth_client()

    try:
        session_result = supabase.auth.get_session()
        session_obj = getattr(session_result, "session", None)
        if session_obj is None and isinstance(session_result, dict):
            session_obj = session_result.get("session")

        user_obj = None
        if session_obj is not None:
            user_obj = getattr(session_obj, "user", None)
            if user_obj is None and isinstance(session_obj, dict):
                user_obj = session_obj.get("user")

        if user_obj is None:
            user_result = supabase.auth.get_user()
            user_obj = getattr(user_result, "user", None)
            if user_obj is None and isinstance(user_result, dict):
                user_obj = user_result.get("user")

        if user_obj is not None:
            store_user_in_state(user_obj)
            return True
    except Exception:
        pass

    clear_user_in_state()
    return False


def handle_oauth_callback() -> None:
    error = safe_get_query_param("error")
    error_description = safe_get_query_param("error_description")
    code = safe_get_query_param("code")

    if error:
        clear_user_in_state()
        st.session_state["last_oauth_code"] = None
        st.session_state["auth_message"] = (
            f"Erro no login Google: {error}"
            + (f" — {error_description}" if error_description else "")
        )
        clear_auth_query_params()
        st.rerun()
        return

    if code:
        if st.session_state.get("last_oauth_code") == code and sync_user_from_current_session(force=True):
            clear_auth_query_params()
            st.rerun()
            return

        supabase = get_supabase_auth_client()

        try:
            result = supabase.auth.exchange_code_for_session({"auth_code": code})
            user_obj = _extract_user_from_auth_response(result)

            if user_obj is None:
                sync_user_from_current_session(force=True)
            else:
                store_user_in_state(user_obj)

            if st.session_state.get("auth_logged_in") and st.session_state.get("auth_user_id"):
                st.session_state["last_oauth_code"] = code
                st.session_state["auth_message"] = "Login efetuado com sucesso."
                clear_auth_query_params()
                st.rerun()
                return

            raise RuntimeError("Usuário não encontrado após concluir o login.")
        except Exception:
            clear_user_in_state()
            st.session_state["last_oauth_code"] = None
            st.session_state["auth_message"] = "Não foi possível concluir o login Google. Tente novamente."
            clear_auth_query_params()
            st.rerun()
            return

    sync_user_from_current_session(force=False)


def start_google_login(force_select_account: bool = False) -> Optional[str]:
    supabase = get_supabase_auth_client()
    redirect_to = build_auth_callback_url()

    options: Dict[str, Any] = {
        "redirect_to": redirect_to,
        "query_params": {"prompt": "select_account" if force_select_account else "select_account"},
    }

    try:
        response = supabase.auth.sign_in_with_oauth(
            {
                "provider": "google",
                "options": options,
            }
        )

        if hasattr(response, "url"):
            url = response.url
        elif isinstance(response, dict):
            url = response.get("url")
        elif isinstance(response, str):
            url = response
        else:
            url = None

        if not url:
            st.session_state["auth_message"] = "Não foi possível gerar a URL de login Google."
            return None

        st.session_state["auth_message"] = None
        st.session_state["last_oauth_code"] = None
        st.session_state["auth_sync_done"] = False
        return url
    except Exception as e:
        st.session_state["auth_message"] = f"Erro ao iniciar login Google: {e}"
        return None


def sign_out_current_user() -> None:
    supabase = get_supabase_auth_client()

    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    for key in LOGOUT_CLEAN_KEYS:
        st.session_state.pop(key, None)

    st.session_state.pop("_supabase_auth_client", None)
    clear_auth_query_params()
    clear_user_in_state()
    st.rerun()
