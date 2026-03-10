from __future__ import annotations

from typing import Optional

import streamlit as st

from core.auth import start_google_login


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
    """
    CTA único de login Google.
    O topo e o bloco inferior usam exatamente esta mesma função.
    """
    auth_url = start_google_login()
    if not auth_url:
        st.error("Não foi possível iniciar o login com Google.")
        return

    if message:
        st.info(message)

    width_style = "width:100%;" if full_width else ""

    st.markdown(
        f"""
        <a href="{auth_url}" target="_self" style="
            display:inline-block;
            {width_style}
            padding:10px 16px;
            border-radius:10px;
            text-decoration:none;
            border:1px solid #d9d9d9;
            font-weight:600;
            text-align:center;
        ">
            {label}
        </a>
        """,
        unsafe_allow_html=True,
    )


def render_google_login_top() -> None:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.caption("Selecione o terreno, faça a análise inicial e gere o relatório completo quando quiser.")

    with col2:
        if _is_logged_in():
            st.success(f"{_user_name()} • {_user_email()}")
        else:
            render_google_login_cta("Entrar com Google", full_width=True)


def render_google_login_box(
    *,
    title: str = "Faça login para continuar",
    message: Optional[str] = None,
) -> None:
    st.markdown("---")
    st.subheader(title)

    if _is_logged_in():
        st.success(f"Você já está logado como {_user_name()}.")
        return

    render_google_login_cta(
        "Entrar com Google",
        full_width=True,
        message=message,
    )
