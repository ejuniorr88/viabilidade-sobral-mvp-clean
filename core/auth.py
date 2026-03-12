from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import urlparse

import streamlit as st
from supabase import Client, create_client


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


def get_supabase_auth_client() -> Client:
    client = st.session_state.get("_supabase_auth_client")
    if client is None:
        client = create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_ANON_KEY"],
        )
        st.session_state["_supabase_auth_client"] = client
    return client


def get_app_url() -> str:
    raw = str(
        st.secrets.get(
            "REDIRECT_URL",
            st.secrets.get("APP_URL", "http://localhost:8501"),
        )
    ).strip()
    if not raw:
        raw = "http://localhost:8501"

    parsed = urlparse(raw)
    if not parsed.scheme or not parsed.netloc:
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
        try:
            params = st.experimental_get_query_params()
            values = params.get(name)
            if not values:
                return None
            return values[0]
        except Exception:
            return None


def clear_auth_query_params() -> None:
    keys = [
        "code",
        "state",
        "error",
        "error_code",
        "error_description",
        "auth_flow",
    ]

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


def _user_from_auth_result(result: Any, client: Client) -> Any:
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
        return user_obj

    try:
        current_user = client.auth.get_user()
        fallback_user = getattr(current_user, "user", None)
        if fallback_user is None and isinstance(current_user, dict):
            fallback_user = current_user.get("user")
        return fallback_user
    except Exception:
        return None


def sync_auth_state(force: bool = False) -> bool:
    if st.session_state.get("auth_sync_done") and not force:
        return bool(st.session_state.get("auth_logged_in"))

    client = get_supabase_auth_client()

    try:
        current_user = client.auth.get_user()
        user_obj = getattr(current_user, "user", None)
        if user_obj is None and isinstance(current_user, dict):
            user_obj = current_user.get("user")

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
        st.session_state["auth_last_error"] = (
            f"Erro no login Google: {error}"
            + (f" — {error_description}" if error_description else "")
        )
        st.session_state.pop("oauth_url", None)
        clear_auth_query_params()
        st.rerun()
        return

    if code:
        client = get_supabase_auth_client()

        try:
            result = client.auth.exchange_code_for_session({"auth_code": code})
            user_obj = _user_from_auth_result(result, client)

            if user_obj is None:
                raise RuntimeError("Usuário não retornado pelo provedor.")

            store_user_in_state(user_obj)
            st.session_state["last_oauth_code"] = code
            st.session_state["auth_message"] = "Login efetuado com sucesso."
            st.session_state.pop("auth_last_error", None)
            st.session_state.pop("oauth_url", None)
            clear_auth_query_params()
            st.rerun()
            return
        except Exception as e:
            clear_user_in_state()
            st.session_state["auth_last_error"] = f"Falha ao concluir login: {e}"
            st.session_state.pop("oauth_url", None)
            clear_auth_query_params()
            st.rerun()
            return

    sync_auth_state(force=False)


def get_auth_url(force_select_account: bool = False) -> Optional[str]:
    client = get_supabase_auth_client()
    options: Dict[str, Any] = {
        "redirect_to": build_auth_callback_url(),
        "query_params": {},
    }

    if force_select_account:
        options["query_params"]["prompt"] = "select_account"

    try:
        response = client.auth.sign_in_with_oauth(
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
            st.session_state["auth_last_error"] = "Não foi possível gerar a URL de login Google."
            return None

        return url
    except Exception as e:
        st.session_state["auth_last_error"] = f"Erro ao iniciar login Google: {e}"
        return None


def start_google_login(force_select_account: bool = False) -> Optional[str]:
    return get_auth_url(force_select_account=force_select_account)


def logout_limpo() -> None:
    client = get_supabase_auth_client()

    try:
        client.auth.sign_out()
    except Exception:
        pass

    keys_to_clear = [
        "auth_user_id",
        "auth_user_email",
        "auth_user_name",
        "auth_logged_in",
        "auth_message",
        "auth_last_error",
        "oauth_url",
        "last_oauth_code",
        "post_login_action",
        "auth_sync_done",
        "show_inline_payments",
        "report_unlocked",
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)

    clear_auth_query_params()
    clear_user_in_state()
    st.rerun()


def sign_out_current_user() -> None:
    logout_limpo()
