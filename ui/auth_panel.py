from __future__ import annotations

from typing import Optional

import streamlit as st

from core.auth import get_auth_url, logout_limpo


def _is_logged_in() -> bool:
    return bool(st.session_state.get("auth_logged_in")) and bool(st.session_state.get("auth_user_id"))


def _user_name() -> str:
    return (
        st.session_state.get("auth_user_name")
        or st.session_state.get("auth_user_email")
        or "Usuário"
    )


def _user_email() -> str:
    return st.session_state.get("auth_user_email") or "-"


def _clear_auth_feedback() -> None:
    st.session_state.pop("auth_last_error", None)
    st.session_state.pop("auth_message", None)


def _render_login_flow(prefix: str, *, force_select_account: bool = False) -> None:
    oauth_key = f"oauth_url_{prefix}"
    generated_url = st.session_state.get(oauth_key)

    if not generated_url:
        if st.button(
            "🚀 Entrar com Google" if not force_select_account else "Trocar usuário",
            key=f"btn_login_generate_{prefix}_{'switch' if force_select_account else 'default'}",
            use_container_width=True,
            type="primary" if not force_select_account else "secondary",
        ):
            _clear_auth_feedback()
            auth_url = get_auth_url(force_select_account=force_select_account)
            if auth_url:
                st.session_state[oauth_key] = auth_url
                st.session_state["oauth_url"] = auth_url
                st.rerun()
        return

    st.info("Sua autenticação foi preparada. Clique abaixo para prosseguir.")
    st.link_button(
        "Confirmar e ir para o Google",
        generated_url,
        use_container_width=True,
        type="primary",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Gerar novo link", key=f"btn_login_regen_{prefix}", use_container_width=True):
            _clear_auth_feedback()
            auth_url = get_auth_url(force_select_account=force_select_account)
            if auth_url:
                st.session_state[oauth_key] = auth_url
                st.session_state["oauth_url"] = auth_url
                st.rerun()
    with col2:
        if st.button("Cancelar", key=f"btn_login_cancel_{prefix}", use_container_width=True):
            st.session_state.pop(oauth_key, None)
            st.session_state.pop("oauth_url", None)
            st.rerun()


def _render_feedback() -> None:
    if st.session_state.get("auth_last_error"):
        st.error(st.session_state["auth_last_error"])
    elif st.session_state.get("auth_message"):
        st.success(st.session_state["auth_message"])


def _render_logged_in_box(prefix: str) -> None:
    _render_feedback()
    st.success(f"{_user_name()} • {_user_email()}")

    col1, col2 = st.columns([1.15, 1])
    with col1:
        if st.button("Sair", key=f"btn_logout_{prefix}", use_container_width=True):
            logout_limpo()
    with col2:
        _render_login_flow(f"{prefix}_switch", force_select_account=True)


def _render_logged_out_box(prefix: str, message: Optional[str] = None) -> None:
    _render_feedback()
    if message:
        st.info(message)
    _render_login_flow(prefix, force_select_account=False)
    st.caption("O login será concluído na mesma aba após o retorno do Google.")


def render_google_login_top() -> None:
    if _is_logged_in():
        _render_logged_in_box("top")
    else:
        _render_logged_out_box("top")


def render_google_login_box(
    *,
    title: str = "Faça login para continuar",
    message: Optional[str] = None,
) -> None:
    st.subheader(title)

    if _is_logged_in():
        _render_logged_in_box("box")
        return

    _render_logged_out_box("box", message=message)
