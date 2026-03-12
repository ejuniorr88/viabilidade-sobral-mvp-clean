
from __future__ import annotations

import json
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import streamlit as st
import streamlit.components.v1 as components
from supabase import Client, create_client


AUTH_STATE_KEYS = [
    "auth_logged_in",
    "auth_user_id",
    "auth_user_email",
    "auth_user_name",
    "auth_message",
    "last_oauth_code",
    "auth_sync_done",
    "_supabase_auth_client",
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
    raw = str(st.secrets.get("APP_URL", "http://localhost:8501")).strip()
    if not raw:
        raw = "http://localhost:8501"

    parsed = urlparse(raw)
    if not parsed.scheme or not parsed.netloc:
        return "http://localhost:8501"

    return raw.rstrip("/")


def build_auth_callback_url() -> str:
    # Mesma aba, mesma rota do app. O callback é tratado pelo próprio app
    # quando chegam ?code=... / ?error=...
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


def browser_redirect(url: str) -> None:
    safe_url = json.dumps(url)
    components.html(
        f"""
        <script>
        const nextUrl = {safe_url};
        const go = () => {{
          try {{ window.top.location.replace(nextUrl); }} catch (e1) {{
            try {{ window.parent.location.replace(nextUrl); }} catch (e2) {{
              window.location.replace(nextUrl);
            }}
          }}
        }};
        go();
        </script>
        """,
        height=0,
    )
    st.stop()


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


def reset_auth_runtime_state(*, keep_message: bool = False) -> None:
    keys = list(AUTH_STATE_KEYS)
    if keep_message:
        keys.remove("auth_message")
    for key in keys:
        st.session_state.pop(key, None)
    if keep_message:
        st.session_state["auth_sync_done"] = False


def sync_user_from_current_session(force: bool = False) -> None:
    if st.session_state.get("auth_sync_done") and not force:
        return

    try:
        supabase = get_supabase_auth_client()
        result = supabase.auth.get_user()
        user_obj = getattr(result, "user", None)
        if user_obj is None and isinstance(result, dict):
            user_obj = result.get("user")

        if user_obj is not None:
            store_user_in_state(user_obj)
        else:
            clear_user_in_state()
    except Exception:
        clear_user_in_state()


def handle_oauth_callback() -> None:
    error = safe_get_query_param("error")
    error_description = safe_get_query_param("error_description")
    code = safe_get_query_param("code")

    if error:
        reset_auth_runtime_state(keep_message=False)
        st.session_state["auth_message"] = (
            f"Erro no login Google: {error}"
            + (f" — {error_description}" if error_description else "")
        )
        clear_auth_query_params()
        browser_redirect(get_app_url())

    if code:
        last_code = st.session_state.get("last_oauth_code")
        if last_code == code and st.session_state.get("auth_logged_in"):
            clear_auth_query_params()
            browser_redirect(get_app_url())

        try:
            supabase = get_supabase_auth_client()
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
                st.session_state["last_oauth_code"] = code
                st.session_state["auth_message"] = "Login efetuado com sucesso."
            else:
                sync_user_from_current_session(force=True)

            if st.session_state.get("auth_logged_in") and st.session_state.get("auth_user_id"):
                clear_auth_query_params()
                browser_redirect(get_app_url())

            reset_auth_runtime_state(keep_message=False)
            st.session_state["auth_message"] = "Não foi possível concluir o login Google."
            clear_auth_query_params()
            browser_redirect(get_app_url())
        except Exception as exc:
            reset_auth_runtime_state(keep_message=False)
            st.session_state["auth_message"] = f"Erro ao concluir o login Google: {exc}"
            clear_auth_query_params()
            browser_redirect(get_app_url())

    sync_user_from_current_session(force=False)


def start_google_login(*, force_select_account: bool = True) -> Optional[str]:
    reset_auth_runtime_state(keep_message=True)
    clear_auth_query_params()

    supabase = get_supabase_auth_client()
    redirect_to = build_auth_callback_url()

    options: Dict[str, Any] = {
        "redirect_to": redirect_to,
        "queryParams": {
            # robustez > conveniência: sempre permite escolher a conta correta
            "prompt": "select_account",
        },
    }

    if not force_select_account:
        # Mantido por compatibilidade; ainda usa select_account para evitar
        # login automático com conta errada em ambiente Streamlit.
        pass

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
    except Exception as exc:
        st.session_state["auth_message"] = f"Erro ao iniciar login Google: {exc}"
        return None


def start_google_login_redirect(*, force_select_account: bool = True) -> None:
    auth_url = start_google_login(force_select_account=force_select_account)
    if not auth_url:
        st.rerun()
        return
    browser_redirect(auth_url)


def sign_out_current_user(*, redirect: bool = True) -> None:
    try:
        supabase = get_supabase_auth_client()
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
    finally:
        reset_auth_runtime_state(keep_message=False)
        clear_auth_query_params()
        clear_user_in_state()

    if redirect:
        browser_redirect(get_app_url())


def switch_google_account() -> None:
    sign_out_current_user(redirect=False)
    start_google_login_redirect(force_select_account=True)
