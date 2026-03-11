from __future__ import annotations

from typing import Optional

import streamlit as st

from core.auth import start_google_login, sign_out_current_user


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


def render_google_login_cta(
    label: str = "Entrar com Google",
    *,
    full_width: bool = False,
    message: Optional[str] = None,
) -> None:
    auth_url = start_google_login()

    if message:
        st.info(message)

    if not auth_url:
        st.error("Não foi possível iniciar o login com Google.")
        return

    st.link_button(label, auth_url, use_container_width=full_width)
    st.caption("O login abrirá em nova aba. Depois volte para esta página.")


def render_google_login_top() -> None:
    if _is_logged_in():
        st.success(f"{_user_name()} • {_user_email()}")
        if st.button("Sair", key="btn_logout_top", use_container_width=True):
            sign_out_current_user()
            st.rerun()
    else:
        render_google_login_cta("Entrar com Google", full_width=True)


def render_google_login_box(
    *,
    title: str = "Faça login para continuar",
    message: Optional[str] = None,
) -> None:
    st.subheader(title)

    if _is_logged_in():
        st.success(f"Você já está logado como {_user_name()}.")
        if st.button("Sair", key="btn_logout_box", use_container_width=True):
            sign_out_current_user()
            st.rerun()
        return

    render_google_login_cta(
        "Entrar com Google para continuar",
        full_width=True,
        message=message,
    )
