from __future__ import annotations

from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from core.auth import get_app_url, safe_get_query_param
from core.credits import get_credit_balance
from ui.auth_panel import render_google_login_box


def card(title: str, value: Any, suffix: str = "") -> None:
    rendered = "—" if value is None or value == "" else f"{value}{suffix}"
    st.markdown(
        f"""
        <div style="padding:12px;border:1px solid #e7e7e7;border-radius:12px;margin-bottom:10px;background:#fff;">
            <div style="font-size:12px;opacity:.75">{title}</div>
            <div style="font-size:20px;font-weight:700">{rendered}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 0.4rem !important;
            padding-bottom: 2rem !important;
            max-width: 100% !important;
        }

        html, body, [data-testid="stAppViewContainer"], .main {
            overflow-x: hidden !important;
        }

        header[data-testid="stHeader"] {
            background: transparent !important;
        }

        div[data-testid="stVerticalBlock"]:has(.vf-header-anchor) {
            background: #081a4b !important;
            border-radius: 18px !important;
            padding: 1.05rem 1.5rem 1rem 1.5rem !important;
            margin: 0 0 1.25rem 0 !important;
            box-shadow: 0 8px 24px rgba(8, 26, 75, 0.10) !important;
        }

        .vf-header-anchor {
            display: none;
        }

        div[data-testid="stVerticalBlock"]:has(.vf-header-anchor) [data-testid="stHorizontalBlock"] {
            align-items: center !important;
            gap: 0.75rem !important;
        }

        .vf-brand {
            font-size: 2rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            line-height: 1;
            color: #ffffff;
            white-space: nowrap;
            padding: 0.1rem 0;
        }

        .vf-brand-dot {
            color: #f59e0b;
        }

        .vf-nav-btn {
            text-align: right;
        }

        div[data-testid="stVerticalBlock"]:has(.vf-header-anchor) .vf-nav-btn .stButton > button[kind="tertiary"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #ffffff !important;
            font-weight: 500 !important;
            font-size: 1rem !important;
            white-space: nowrap !important;
            padding: 0 !important;
            min-height: auto !important;
            line-height: 1.2 !important;
            justify-content: flex-end !important;
        }

        div[data-testid="stVerticalBlock"]:has(.vf-header-anchor) .vf-nav-btn .stButton > button[kind="tertiary"]:hover,
        div[data-testid="stVerticalBlock"]:has(.vf-header-anchor) .vf-nav-btn .stButton > button[kind="tertiary"]:focus,
        div[data-testid="stVerticalBlock"]:has(.vf-header-anchor) .vf-nav-btn .stButton > button[kind="tertiary"]:focus-visible,
        div[data-testid="stVerticalBlock"]:has(.vf-header-anchor) .vf-nav-btn .stButton > button[kind="tertiary"]:active {
            color: #ffffff !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
        }

        @media (max-width: 900px) {
            div[data-testid="stVerticalBlock"]:has(.vf-header-anchor) {
                padding: 0.9rem 1rem 0.9rem 1rem !important;
            }

            .vf-brand {
                font-size: 1.55rem;
                margin-bottom: 0.45rem;
            }

            div[data-testid="stVerticalBlock"]:has(.vf-header-anchor) .vf-nav-btn .stButton > button[kind="tertiary"] {
                font-size: 0.92rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_top_nav() -> None:
    with st.container():
        st.markdown('<div class="vf-header-anchor"></div>', unsafe_allow_html=True)
        brand_col, nav1, nav2, nav3, nav4 = st.columns([5.2, 1.35, 1.55, 0.95, 1.6], gap="medium")

        with brand_col:
            st.markdown(
                '<div class="vf-brand">Viabilidade-Fácil<span class="vf-brand-dot">.</span></div>',
                unsafe_allow_html=True,
            )

        with nav1:
            st.markdown('<div class="vf-nav-btn">', unsafe_allow_html=True)
            st.button("Como funciona", key="vf_nav_how", type="tertiary", use_container_width=False)
            st.markdown('</div>', unsafe_allow_html=True)

        with nav2:
            st.markdown('<div class="vf-nav-btn">', unsafe_allow_html=True)
            if st.button("Área do cliente", key="vf_nav_client", type="tertiary", use_container_width=False):
                st.session_state["show_client_area"] = True
                if not st.session_state.get("auth_logged_in"):
                    st.session_state["post_login_action"] = "open_client_area"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with nav3:
            st.markdown('<div class="vf-nav-btn">', unsafe_allow_html=True)
            st.button("Planos", key="vf_nav_plans", type="tertiary", use_container_width=False)
            st.markdown('</div>', unsafe_allow_html=True)

        with nav4:
            st.markdown('<div class="vf-nav-btn">', unsafe_allow_html=True)
            st.button("Dúvida e suporte", key="vf_nav_support", type="tertiary", use_container_width=False)
            st.markdown('</div>', unsafe_allow_html=True)


def render_wallet_summary() -> None:
    user_name = st.session_state.get("auth_user_name") or st.session_state.get("auth_name") or "—"
    user_email = st.session_state.get("auth_user_email") or st.session_state.get("auth_email") or "—"
    user_id = st.session_state.get("auth_user_id")

    balance = "—"
    if user_id:
        try:
            balance = str(get_credit_balance(user_id))
        except Exception:
            balance = "—"

    st.markdown("**Minha carteira**")
    c1, c2, c3 = st.columns(3)
    with c1:
        card("Usuário", user_name)
    with c2:
        card("E-mail", user_email)
    with c3:
        card("Saldo de créditos", balance)



def render_login_gate_block() -> None:
    render_google_login_box(
        title="Faça login para continuar",
        message="Para liberar a pesquisa de viabilidade, entre com sua conta Google.",
        context="shell_gate",
    )



def render_auth_callback_bridge() -> None:
    code = safe_get_query_param("code") or ""
    error = safe_get_query_param("error") or ""
    error_code = safe_get_query_param("error_code") or ""
    error_description = safe_get_query_param("error_description") or ""
    state = safe_get_query_param("state") or ""
    app_url = get_app_url()

    st.markdown("## Concluindo seu login...")
    st.caption("Aguarde alguns segundos. Se a aba principal não atualizar, ela será redirecionada automaticamente.")

    bridge_html = f"""
    <script>
    (function() {{
        const appUrl = {app_url!r};
        const params = new URLSearchParams();
        const code = {code!r};
        const error = {error!r};
        const errorCode = {error_code!r};
        const errorDescription = {error_description!r};
        const state = {state!r};

        if (code) params.set("code", code);
        if (error) params.set("error", error);
        if (errorCode) params.set("error_code", errorCode);
        if (errorDescription) params.set("error_description", errorDescription);
        if (state) params.set("state", state);

        const destination = params.toString() ? `${{appUrl}}/?${{params.toString()}}` : appUrl;

        try {{
            if (window.opener && !window.opener.closed) {{
                window.opener.location.replace(destination);
                window.close();
                return;
            }}
        }} catch (e) {{}}

        window.location.replace(destination);
    }})();
    </script>
    """

    components.html(bridge_html, height=0)
    st.stop()
