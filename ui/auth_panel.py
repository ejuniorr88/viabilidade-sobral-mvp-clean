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
    # Mantido o mesmo fluxo estável:
    # gera a URL via core.auth.start_google_login()
    # e abre em nova aba via target="_blank"
    auth_url = start_google_login()
    if not auth_url:
        st.error("Não foi possível iniciar o login com Google.")
        return

    if message:
        st.info(message)

    width_style = "width:100%;" if full_width else ""

    st.markdown(
        f"""
        <a href="{auth_url}" target="_blank" rel="noopener noreferrer" style="
            display:inline-block;
            {width_style}
            padding:12px 16px;
            border-radius:12px;
            text-decoration:none;
            border:1px solid #d9d9d9;
            font-weight:700;
            text-align:center;
            background:#ffffff;
            color:#222222;
            box-shadow:0 1px 4px rgba(0,0,0,0.06);
        ">
            🔐 {label}
        </a>
        """,
        unsafe_allow_html=True,
    )

    st.caption("O login abrirá em uma nova aba. Depois de concluir, volte para esta página.")


def render_google_login_top() -> None:
    # Regra do patch:
    # este bloco deve cuidar SOMENTE de login/logout.
    # A frase institucional deve ficar fora daqui para não duplicar.
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
    st.markdown('<div id="login-required-box"></div>', unsafe_allow_html=True)
    st.markdown("---")
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
