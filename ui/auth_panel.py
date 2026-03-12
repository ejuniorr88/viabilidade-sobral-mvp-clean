
from __future__ import annotations

from typing import Optional

import streamlit as st

from core.auth import sign_out_current_user, start_google_login_redirect, switch_google_account


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
    force_select_account: bool = True,
    subtle: bool = False,
) -> None:
    if message:
        st.info(message)

    clicked = st.button(
        label,
        use_container_width=full_width,
        key=f"auth_btn_{label}_{'subtle' if subtle else 'main'}_{'full' if full_width else 'auto'}",
        type="secondary",
    )
    if clicked:
        start_google_login_redirect(force_select_account=force_select_account)

    if not subtle:
        st.caption("O login será concluído nesta mesma aba.")


def _render_logged_in_box(prefix: str) -> None:
    st.success(f"{_user_name()} • {_user_email()}")

    col1, col2 = st.columns([1.25, 1])

    with col1:
        if st.button("Sair", key=f"btn_logout_{prefix}", use_container_width=True):
            sign_out_current_user()

    with col2:
        if st.button("Trocar usuário", key=f"btn_switch_user_{prefix}", use_container_width=True):
            switch_google_account()


def _render_logged_out_box(prefix: str) -> None:
    render_google_login_cta(
        "Entrar com Google",
        full_width=True,
        force_select_account=True,
    )


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

    if message:
        st.info(message)

    if _is_logged_in():
        _render_logged_in_box("box")
        return

    _render_logged_out_box("box")
