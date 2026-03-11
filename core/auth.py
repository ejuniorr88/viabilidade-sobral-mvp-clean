from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import urlparse

import streamlit as st
from supabase import Client, create_client


@st.cache_resource(show_spinner=False)
def get_supabase_auth_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)


def get_app_url() -> str:
    raw = st.secrets.get("APP_URL", "http://localhost:8501").strip()
    if not raw:
        raw = "http://localhost:8501"

    parsed = urlparse(raw)
    if not parsed.scheme or not parsed.netloc:
        return "http://localhost:8501"

    return f"{parsed.scheme}://{parsed.netloc}"


def get_google_web_client_id() -> str:
    return st.secrets["GOOGLE_WEB_CLIENT_ID"]


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
    keys_to_remove = [
        "code",
        "error",
        "error_code",
        "error_description",
        "state",
        "google_id_token",
    ]

    try:
        for k in keys_to_remove:
            try:
                del st.query_params[k]
            except Exception:
                pass
    except Exception:
        try:
            current = st.experimental_get_query_params()
            cleaned = {k: v for k, v in current.items() if k not in keys_to_remove}
            st.experimental_set_query_params(**cleaned)
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


def clear_user_in_state() -> None:
    st.session_state["auth_logged_in"] = False
    st.session_state["auth_user_email"] = None
    st.session_state["auth_user_name"] = None
    st.session_state["auth_user_id"] = None


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

    clear_user_in_state()


def _complete_sign_in_with_google_id_token(id_token: str) -> bool:
    supabase = get_supabase_auth_client()

    response = supabase.auth.sign_in_with_id_token(
        {
            "provider": "google",
            "token": id_token,
        }
    )

    user_obj = getattr(response, "user", None)
    session_obj = getattr(response, "session", None)

    if user_obj is None and isinstance(response, dict):
        user_obj = response.get("user")
        session_obj = response.get("session")

    if user_obj is None and session_obj is not None:
        user_obj = getattr(session_obj, "user", None)
        if user_obj is None and isinstance(session_obj, dict):
            user_obj = session_obj.get("user")

    if user_obj is None:
        sync_user_from_current_session()
        return bool(st.session_state.get("auth_logged_in"))

    store_user_in_state(user_obj)
    return True


def handle_oauth_callback() -> None:
    """
    Agora prioriza login via google_id_token retornado pelo botão oficial do Google.
    Mantém fallback para o fluxo antigo com code.
    """
    error = safe_get_query_param("error")
    error_description = safe_get_query_param("error_description")
    google_id_token = safe_get_query_param("google_id_token")
    code = safe_get_query_param("code")

    if error:
        clear_user_in_state()
        st.session_state["auth_message"] = (
            f"Erro no retorno do login Google: {error}"
            + (f" — {error_description}" if error_description else "")
        )
        clear_auth_query_params()
        return

    if google_id_token:
        if st.session_state.get("last_google_id_token") == google_id_token:
            return

        try:
            ok = _complete_sign_in_with_google_id_token(google_id_token)
            if ok:
                st.session_state["auth_message"] = "Login efetuado com sucesso."
                st.session_state["last_google_id_token"] = google_id_token
            else:
                clear_user_in_state()
                st.session_state["auth_message"] = "Não foi possível concluir o login com Google."
        except Exception as e:
            clear_user_in_state()
            st.session_state["auth_message"] = f"Erro ao concluir o login Google: {e}"

        clear_auth_query_params()
        st.rerun()
        return

    # Fallback legado, caso você ainda use alguma rota antiga
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

        if user_obj is None:
            sync_user_from_current_session()
            if st.session_state.get("auth_logged_in"):
                st.session_state["auth_message"] = "Login efetuado com sucesso."
                st.session_state["last_oauth_code"] = code
                clear_auth_query_params()
                st.rerun()
                return

        if user_obj is not None:
            store_user_in_state(user_obj)
            st.session_state["auth_message"] = "Login efetuado com sucesso."
            st.session_state["last_oauth_code"] = code
            clear_auth_query_params()
            st.rerun()
        else:
            clear_user_in_state()
            st.session_state["auth_message"] = (
                "O Google retornou ao app, mas não foi possível identificar o usuário logado."
            )
            clear_auth_query_params()

    except Exception as e:
        clear_user_in_state()
        st.session_state["auth_message"] = f"Erro ao concluir o login Google: {e}"
        clear_auth_query_params()


def start_google_login() -> Optional[str]:
    """
    Mantido só por compatibilidade. O fluxo novo usa botão GIS, não redirect OAuth.
    """
    return get_app_url()


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
        "last_google_id_token",
        "post_login_action",
        "pending_login_reason",
    ]:
        st.session_state.pop(key, None)

    clear_auth_query_params()
    clear_user_in_state()
