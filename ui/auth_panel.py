from __future__ import annotations

from typing import Optional

import streamlit as st

from components.auth_popup_component import render_auth_popup_button
from core.auth import start_google_login, sign_out_current_user
from ui.auth_login_keys import build_auth_popup_key


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
    force_select_account: bool = False,
    subtle: bool = False,
    context: str = "default",
) -> None:
    auth_url = start_google_login(force_select_account=force_select_account)

    if message:
        st.info(message)

    if not auth_url:
        st.error("Não foi possível iniciar o login com Google.")
        return

    clear_browser_token = bool(st.session_state.pop("auth_clear_browser_token", False))

    token = render_auth_popup_button(
        auth_url=auth_url,
        label=label,
        subtle=subtle,
        key=build_auth_popup_key(
            context=context,
            label=label,
            subtle=subtle,
            force_select_account=force_select_account,
        ),
        restore_token=True,
        clear_browser_token=clear_browser_token,
    )

    if token:
        current_token = st.session_state.get("auth_external_access_token")
        already_logged = bool(st.session_state.get("auth_logged_in") and st.session_state.get("auth_user_id"))
        if token != current_token or not already_logged:
            st.session_state["auth_external_access_token"] = token
            st.session_state["auth_sync_done"] = False
            st.rerun()

    if not subtle:
        st.caption("O login abrirá em uma janela popup segura.")


def _render_logged_in_box(prefix: str) -> None:
    st.success(f"{_user_name()} • {_user_email()}")

    col1, col2 = st.columns([1.25, 1])

    with col1:
        if st.button("Sair", key=f"btn_logout_{prefix}", use_container_width=True):
            st.session_state["auth_clear_browser_token"] = True
            sign_out_current_user()
            st.rerun()

    with col2:
        render_google_login_cta(
            "Trocar usuário",
            full_width=True,
            force_select_account=True,
            subtle=True,
            context=f"{prefix}_swap_user",
        )


def _render_logged_out_box(prefix: str) -> None:
    render_google_login_cta(
        "Entrar com Google",
        full_width=True,
        force_select_account=False,
        context=f"{prefix}_login",
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
    context: str = "box",
) -> None:
    st.subheader(title)

    if message:
        st.info(message)

    if _is_logged_in():
        _render_logged_in_box(context)
        return

    _render_logged_out_box(context)
