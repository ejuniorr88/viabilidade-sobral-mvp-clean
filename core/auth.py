from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st
from supabase import Client, create_client


@st.cache_resource(show_spinner=False)
def get_supabase_auth_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)


def get_app_url() -> str:
    return st.secrets.get("APP_URL", "http://localhost:8501")


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


def clear_auth_query_params() -> None:
    try:
        st.query_params.clear()
    except Exception:
        try:
            st.experimental_set_query_params()
        except Exception:
            pass


def extract_user_fields(user_obj: Any) -> Dict[str, Optional[str]]:
    email = None
    name = None
    uid = None

    if user_obj is None:
        return {"email": None, "name": None, "id": None}

    if isinstance(user_obj, dict):
        email = user_obj.get("email")
        uid = user_obj.get("id")
        meta = user_obj.get("user_metadata") or {}
        name = meta.get("full_name") or meta.get("name")
        return {"email": email, "name": name, "id": uid}

    email = getattr(user_obj, "email", None)
    uid = getattr(user_obj, "id", None)
    meta = getattr(user_obj, "user_metadata", None) or {}
    if isinstance(meta, dict):
        name = meta.get("full_name") or meta.get("name")
    else:
        name = getattr(meta, "full_name", None) or getattr(meta, "name", None)

    return {"email": email, "name": name, "id": uid}


def store_user_in_state(user_obj: Any) -> None:
    info = extract_user_fields(user_obj)
    st.session_state["auth_logged_in"] = bool(info.get("id") or info.get("email"))
    st.session_state["auth_user_email"] = info.get("email")
    st.session_state["auth_user_name"] = info.get("name")
    st.session_state["auth_user_id"] = info.get("id")


def sync_user_from_current_session() -> None:
    supabase = get_supabase_auth_client()

    try:
        user_response = supabase.auth.get_user()
        user_obj = getattr(user_response, "user", None)
        if user_obj is None and isinstance(user_response, dict):
            user_obj = user_response.get("user")
        if user_obj is not None:
            store_user_in_state(user_obj)
            return
    except Exception:
        pass

    if "auth_logged_in" not in st.session_state:
        st.session_state["auth_logged_in"] = False
        st.session_state["auth_user_email"] = None
        st.session_state["auth_user_name"] = None
        st.session_state["auth_user_id"] = None


def handle_oauth_callback() -> None:
    code = safe_get_query_param("code")
    if not code:
        return

    if st.session_state.get("last_oauth_code") == code:
        return

    supabase = get_supabase_auth_client()

    try:
        response = supabase.auth.exchange_code_for_session({"auth_code": code})
        user_obj = getattr(response, "user", None)
        session_obj = getattr(response, "session", None)

        if user_obj is None and isinstance(response, dict):
            user_obj = response.get("user")
            session_obj = response.get("session")

        if user_obj is None and session_obj is not None:
            user_obj = getattr(session_obj, "user", None)
            if user_obj is None and isinstance(session_obj, dict):
                user_obj = session_obj.get("user")

        if user_obj is not None:
            store_user_in_state(user_obj)
            st.session_state["auth_message"] = "Login efetuado com sucesso."
            st.session_state["last_oauth_code"] = code
            clear_auth_query_params()
            st.rerun()
        else:
            st.session_state["auth_logged_in"] = False
            st.session_state["auth_message"] = (
                "O Google retornou ao app, mas não foi possível identificar o usuário logado."
            )
    except Exception as e:
        st.session_state["auth_logged_in"] = False
        st.session_state["auth_message"] = f"Erro ao concluir o login Google: {e}"


def start_google_login() -> Optional[str]:
    supabase = get_supabase_auth_client()
    response = supabase.auth.sign_in_with_oauth(
        {
            "provider": "google",
            "options": {
                "redirect_to": get_app_url(),
            },
        }
    )

    if hasattr(response, "url"):
        return response.url
    if isinstance(response, dict):
        return response.get("url")
    return None


def sign_out_current_user() -> None:
    supabase = get_supabase_auth_client()
    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    for key in [
        "auth_logged_in",
        "auth_user_email",
        "auth_user_name",
        "auth_user_id",
        "auth_message",
        "last_oauth_code",
    ]:
        st.session_state.pop(key, None)

    clear_auth_query_params()
