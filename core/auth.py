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


def _push_auth_debug(step: str, data: Optional[Dict[str, Any]] = None) -> None:
    logs = st.session_state.get("_auth_debug_logs", [])
    logs.append(
        {
            "step": step,
            "data": data or {},
        }
    )
    st.session_state["_auth_debug_logs"] = logs[-20:]


def get_auth_debug_logs() -> list[dict]:
    return st.session_state.get("_auth_debug_logs", [])


def clear_auth_debug_logs() -> None:
    st.session_state["_auth_debug_logs"] = []


def get_app_url() -> str:
    """
    Usa APP_URL das secrets e normaliza para evitar diferenças bobas
    de barra final / caminho vazio.
    """
    raw = st.secrets.get("APP_URL", "http://localhost:8501").strip()
    if not raw:
        raw = "http://localhost:8501"

    parsed = urlparse(raw)
    if not parsed.scheme or not parsed.netloc:
        _push_auth_debug("get_app_url_invalid", {"raw": raw})
        return "http://localhost:8501"

    normalized = f"{parsed.scheme}://{parsed.netloc}"
    _push_auth_debug("get_app_url", {"raw": raw, "normalized": normalized})
    return normalized


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


def get_all_auth_query_params() -> Dict[str, Any]:
    keys = ["code", "error", "error_code", "error_description", "state"]
    result: Dict[str, Any] = {}
    for key in keys:
        value = safe_get_query_param(key)
        if value is not None:
            result[key] = value
    return result


def clear_auth_query_params() -> None:
    keys_to_remove = [
        "code",
        "error",
        "error_code",
        "error_description",
        "state",
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

    _push_auth_debug("clear_auth_query_params", {})


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
    _push_auth_debug("store_user_in_state", info)


def clear_user_in_state() -> None:
    st.session_state["auth_logged_in"] = False
    st.session_state["auth_user_email"] = None
    st.session_state["auth_user_name"] = None
    st.session_state["auth_user_id"] = None
    _push_auth_debug("clear_user_in_state", {})


def sync_user_from_current_session() -> None:
    supabase = get_supabase_auth_client()

    try:
        user_response = supabase.auth.get_user()
        user_obj = getattr(user_response, "user", None)
        if user_obj is None and isinstance(user_response, dict):
            user_obj = user_response.get("user")

        if user_obj is not None:
            _push_auth_debug("sync_user_from_current_session_found", extract_user_fields(user_obj))
            store_user_in_state(user_obj)
            return

        _push_auth_debug("sync_user_from_current_session_empty", {})
    except Exception as e:
        _push_auth_debug("sync_user_from_current_session_error", {"error": str(e)})

    clear_user_in_state()


def handle_oauth_callback() -> None:
    """
    Processa callback do Google vindo do Supabase.
    Também trata cenários de erro retornados na query string.

    Patch importante:
    - se não houver `code` na URL, tentamos sincronizar a sessão atual.
    - isso ajuda o app a continuar reconhecendo o usuário logado
      depois que ele volta para a aba principal ou recarrega a página.
    """
    params = get_all_auth_query_params()
    _push_auth_debug("handle_oauth_callback_enter", params)

    error = safe_get_query_param("error")
    error_description = safe_get_query_param("error_description")
    code = safe_get_query_param("code")

    if error:
        clear_user_in_state()
        st.session_state["auth_message"] = (
            f"Erro no retorno do login Google: {error}"
            + (f" — {error_description}" if error_description else "")
        )
        _push_auth_debug(
            "handle_oauth_callback_error_param",
            {
                "error": error,
                "error_description": error_description,
            },
        )
        clear_auth_query_params()
        return

    # Mudança principal:
    # antes retornava imediatamente.
    # agora sincroniza a sessão existente quando a página abre sem `code`.
    if not code:
        _push_auth_debug("handle_oauth_callback_no_code", {})
        sync_user_from_current_session()
        return

    if st.session_state.get("last_oauth_code") == code:
        _push_auth_debug("handle_oauth_callback_duplicate_code", {"code": code[:12] + "..."})
        return

    supabase = get_supabase_auth_client()

    try:
        _push_auth_debug("exchange_code_for_session_start", {"code": code[:12] + "..."})
        response = supabase.auth.exchange_code_for_session({"auth_code": code})
        _push_auth_debug("exchange_code_for_session_ok", {"response_type": str(type(response))})

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
            _push_auth_debug("exchange_code_for_session_no_user_direct", {})
            sync_user_from_current_session()
            if st.session_state.get("auth_logged_in"):
                st.session_state["auth_message"] = "Login efetuado com sucesso."
                st.session_state["last_oauth_code"] = code
                _push_auth_debug("oauth_callback_login_success_via_sync", {})
                clear_auth_query_params()
                st.rerun()
                return

        if user_obj is not None:
            store_user_in_state(user_obj)
            st.session_state["auth_message"] = "Login efetuado com sucesso."
            st.session_state["last_oauth_code"] = code
            _push_auth_debug("oauth_callback_login_success_direct", {})
            clear_auth_query_params()
            st.rerun()
        else:
            clear_user_in_state()
            st.session_state["auth_message"] = (
                "O Google retornou ao app, mas não foi possível identificar o usuário logado."
            )
            _push_auth_debug("oauth_callback_no_user_after_exchange", {})
            clear_auth_query_params()

    except Exception as e:
        clear_user_in_state()
        st.session_state["auth_message"] = f"Erro ao concluir o login Google: {e}"
        _push_auth_debug("exchange_code_for_session_exception", {"error": str(e)})
        clear_auth_query_params()


def start_google_login() -> Optional[str]:
    """
    Inicia o login Google via Supabase.
    """
    supabase = get_supabase_auth_client()
    redirect_to = get_app_url()

    _push_auth_debug("start_google_login_before", {"redirect_to": redirect_to})

    try:
        response = supabase.auth.sign_in_with_oauth(
            {
                "provider": "google",
                "options": {
                    "redirect_to": redirect_to,
                },
            }
        )

        if hasattr(response, "url"):
            url = response.url
            _push_auth_debug("start_google_login_response_attr", {"url": url})
            return url

        if isinstance(response, dict):
            url = response.get("url")
            _push_auth_debug("start_google_login_response_dict", {"url": url})
            return url

        _push_auth_debug("start_google_login_response_unknown", {"response_type": str(type(response))})
        return None

    except Exception as e:
        _push_auth_debug("start_google_login_exception", {"error": str(e)})
        st.session_state["auth_message"] = f"Erro ao iniciar login Google: {e}"
        return None


def sign_out_current_user() -> None:
    supabase = get_supabase_auth_client()

    try:
        supabase.auth.sign_out()
        _push_auth_debug("sign_out_current_user_ok", {})
    except Exception as e:
        _push_auth_debug("sign_out_current_user_error", {"error": str(e)})

    for key in [
        "auth_logged_in",
        "auth_user_email",
        "auth_user_name",
        "auth_user_id",
        "auth_message",
        "last_oauth_code",
        "post_login_action",
        "pending_login_reason",
        "google_login_url",
    ]:
        st.session_state.pop(key, None)

    clear_auth_query_params()
    clear_user_in_state()
