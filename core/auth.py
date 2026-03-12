from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse

import streamlit as st
from supabase import Client, create_client


def get_supabase_auth_client() -> Client:
    client = st.session_state.get("_supabase_auth_client")
    if client is None:
        client = create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_ANON_KEY"],
        )
        st.session_state["_supabase_auth_client"] = client
    return client


def _push_auth_debug(step: str, data: Optional[Dict[str, Any]] = None) -> None:
    logs = st.session_state.get("_auth_debug_logs", [])
    logs.append({"step": step, "data": data or {}})
    st.session_state["_auth_debug_logs"] = logs[-50:]


def get_auth_debug_logs() -> list[dict]:
    return st.session_state.get("_auth_debug_logs", [])


def clear_auth_debug_logs() -> None:
    st.session_state["_auth_debug_logs"] = []


def get_app_url() -> str:
    raw = str(st.secrets.get("APP_URL", "http://localhost:8501")).strip()
    if not raw:
        raw = "http://localhost:8501"

    parsed = urlparse(raw)
    if not parsed.scheme or not parsed.netloc:
        _push_auth_debug("get_app_url_invalid", {"raw": raw})
        return "http://localhost:8501"

    return raw.rstrip("/")


def build_auth_callback_url() -> str:
    return get_app_url()


def safe_get_query_param(name: str) -> Optional[str]:
    try:
        value = st.query_params.get(name)
        if isinstance(value, list):
            return value[0] if value else None
        return value
    except Exception:
        params = st.experimental_get_query_params()
        values = params.get(name)
        if not values:
            return None
        return values[0]


def clear_auth_query_params(*, keep_auth_flow: bool = False) -> None:
    keys = [
        "code",
        "state",
        "error",
        "error_code",
        "error_description",
    ]

    if not keep_auth_flow:
        keys.append("auth_flow")

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


def sync_user_from_current_session(force: bool = False) -> None:
    if st.session_state.get("auth_sync_done") and not force:
        return

    supabase = get_supabase_auth_client()

    try:
        result = supabase.auth.get_user()
        user_obj = getattr(result, "user", None)
        if user_obj is None and isinstance(result, dict):
            user_obj = result.get("user")

        if user_obj is not None:
            store_user_in_state(user_obj)
        else:
            clear_user_in_state()
            st.session_state["auth_sync_done"] = True
    except Exception:
        clear_user_in_state()
        st.session_state["auth_sync_done"] = True


def is_auth_callback_mode() -> bool:
    if safe_get_query_param("code"):
        return True
    if safe_get_query_param("error"):
        return True
    return False


def handle_oauth_callback() -> None:
    error = safe_get_query_param("error")
    error_description = safe_get_query_param("error_description")
    code = safe_get_query_param("code")

    if error:
        clear_user_in_state()
        st.session_state["auth_message"] = (
            f"Erro no login Google: {error}"
            + (f" — {error_description}" if error_description else "")
        )
        # remove TUDO, inclusive auth_flow, para não ficar preso na tela de callback
        clear_auth_query_params(keep_auth_flow=False)
        st.rerun()
        return

    if code:
        last_code = st.session_state.get("last_oauth_code")
        if last_code == code:
            sync_user_from_current_session(force=True)
            if st.session_state.get("auth_logged_in"):
                clear_auth_query_params(keep_auth_flow=False)
                st.rerun()
            return

        supabase = get_supabase_auth_client()

        try:
            result = supabase.auth.exchange_code_for_session({"auth_code": code})

            user_obj = getattr(result, "user", None)
            session_obj = getattr(result, "session", None)

            if user_obj is None and isinstance(result, dict):
                user_obj = result.get("user")
                session_obj = result.get("session")

            if user_obj is None and session_obj is not None:
                user_obj = getattr(session_obj, "user", None)
                if user_obj is None and isinstance(session_obj, dict):
                    user_obj = session_obj.get("user")

            if user_obj is not None:
                store_user_in_state(user_obj)
            else:
                sync_user_from_current_session(force=True)

            if st.session_state.get("auth_logged_in"):
                st.session_state["last_oauth_code"] = code
                st.session_state["auth_message"] = "Login efetuado com sucesso."
                # remove TUDO, inclusive auth_flow, para sair do modo callback
                clear_auth_query_params(keep_auth_flow=False)
                st.rerun()
                return

            clear_user_in_state()
            st.session_state["auth_message"] = "Não foi possível concluir o login Google."
            clear_auth_query_params(keep_auth_flow=False)
            st.rerun()
            return

        except Exception as e:
            clear_user_in_state()
            st.session_state["auth_message"] = f"Erro ao concluir o login Google: {e}"
            clear_auth_query_params(keep_auth_flow=False)
            st.rerun()
            return

    if st.session_state.get("auth_logged_in") and st.session_state.get("auth_user_id"):
        return

    sync_user_from_current_session(force=False)


def start_google_login(force_select_account: bool = False) -> Optional[str]:
    supabase = get_supabase_auth_client()
    redirect_to = build_auth_callback_url()

    options: Dict[str, Any] = {
        "redirect_to": redirect_to,
    }

    if force_select_account:
        options["queryParams"] = {
            "prompt": "select_account",
        }

    try:
        response = supabase.auth.sign_in_with_oauth(
            {
                "provider": "google",
                "options": options,
            }
        )

        url: Optional[str] = None

        if hasattr(response, "url"):
            url = response.url
        elif isinstance(response, dict):
            url = response.get("url")
        elif isinstance(response, str):
            url = response

        if not url:
            st.session_state["auth_message"] = "Não foi possível gerar a URL de login Google."
            return None

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

    for key in [
        "auth_logged_in",
        "auth_user_id",
        "auth_user_email",
        "auth_user_name",
        "auth_message",
        "last_oauth_code",
        "post_login_action",
        "auth_sync_done",
        "_supabase_auth_client",
    ]:
        st.session_state.pop(key, None)

    clear_auth_query_params()
    clear_user_in_state()
