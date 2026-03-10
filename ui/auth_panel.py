from __future__ import annotations

from typing import Optional

import streamlit as st


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


def _get_google_login_url() -> Optional[str]:
    try:
        from core.auth import start_google_login
        return start_google_login()
    except Exception:
        return None


def _run_logout() -> None:
    """
    Tenta usar a rotina real do projeto. Se não existir, faz fallback
    limpando a sessão local do Streamlit.
    """
    logout_called = False

    try:
        from core import auth as auth_module  # type: ignore

        for fn_name in ("logout", "sign_out", "do_logout", "handle_logout"):
            fn = getattr(auth_module, fn_name, None)
            if callable(fn):
                fn()
                logout_called = True
                break
    except Exception:
        pass

    # fallback local
    keys_to_clear = [
        "auth_logged_in",
        "auth_user_id",
        "auth_user_email",
        "auth_user_name",
        "post_login_action",
        "pending_login_reason",
        "pending_report_after_payment",
        "payments_focus_mode",
        "report_unlocked",
        "free_calc_done",
        "current_payment_id",
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)

    if logout_called:
        try:
            st.rerun()
        except Exception:
            pass
    else:
        st.rerun()


def render_google_login_cta(
    label: str = "Entrar com Google",
    *,
    full_width: bool = False,
    message: Optional[str] = None,
) -> None:
    auth_url = _get_google_login_url()
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
            if st.button("Sair", key="btn_logout_top", use_container_width=True):
                _run_logout()
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
        if st.button("Sair", key="btn_logout_box", use_container_width=True):
            _run_logout()
        return

    render_google_login_cta(
        "Entrar com Google",
        full_width=True,
        message=message,
    )
