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


def _redirect_same_tab(url: str) -> None:
    safe_url = url.replace('"', '&quot;')
    st.markdown(
        f'''
        <script>
        window.location.assign("{safe_url}");
        </script>
        <meta http-equiv="refresh" content="0; url={safe_url}">
        ''',
        unsafe_allow_html=True,
    )
    st.stop()


def _render_login_button(
    label: str,
    auth_url: str,
    *,
    full_width: bool = False,
    subtle: bool = False,
    key: str,
) -> None:
    if st.button(label, key=key, use_container_width=full_width, type="secondary"):
        _redirect_same_tab(auth_url)


def render_google_login_cta(
    label: str = "Entrar com Google",
    *,
    full_width: bool = False,
    message: Optional[str] = None,
    force_select_account: bool = False,
    subtle: bool = False,
    key: str = "google_login_cta",
) -> None:
    auth_url = start_google_login(force_select_account=force_select_account)

    if message:
        st.info(message)

    if not auth_url:
        st.error("Não foi possível iniciar o login com Google.")
        return

    _render_login_button(
        label,
        auth_url,
        full_width=full_width,
        subtle=subtle,
        key=key,
    )

    if not subtle:
        st.caption("O login será concluído nesta mesma aba.")


def _render_logged_in_box(prefix: str) -> None:
    st.success(f"{_user_name()} • {_user_email()}")

    col1, col2 = st.columns([1.25, 1])

    with col1:
        if st.button("Sair", key=f"btn_logout_{prefix}", use_container_width=True):
            sign_out_current_user()
            st.rerun()

    with col2:
        render_google_login_cta(
            "Trocar usuário",
            full_width=True,
            force_select_account=True,
            subtle=True,
            key=f"btn_switch_user_{prefix}",
        )


def _render_logged_out_box(prefix: str) -> None:
    render_google_login_cta(
        "Entrar com Google",
        full_width=True,
        force_select_account=False,
        key=f"btn_login_{prefix}",
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
