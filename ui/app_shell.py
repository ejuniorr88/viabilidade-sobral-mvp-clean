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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Montserrat:wght@500;600;700;800&display=swap');

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

        div[data-testid="stVerticalBlock"]:has(#vf-top-nav-anchor) {
            background: rgba(11, 19, 43, 0.96) !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
            padding: 18px 26px 16px 26px !important;
            margin: 0 0 1.45rem 0 !important;
            border-radius: 0 !important;
            box-shadow: 0 8px 22px rgba(11, 19, 43, 0.16) !important;
        }

        div[data-testid="stVerticalBlock"]:has(#vf-top-nav-anchor) [data-testid="column"] {
            display: flex !important;
            align-items: center !important;
        }

        .vf-brand {
            font-family: 'Montserrat', sans-serif !important;
            font-size: 24px;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: 1px;
            line-height: 1;
            white-space: nowrap;
        }

        .vf-brand span {
            color: #D68910;
        }

        div[data-testid="stVerticalBlock"]:has(#vf-top-nav-anchor) .vf-nav-btn .stButton > button[kind="tertiary"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: rgba(255,255,255,0.86) !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 500 !important;
            font-size: 14px !important;
            white-space: nowrap !important;
            padding: 0 !important;
            min-height: auto !important;
            line-height: 1.1 !important;
            justify-content: center !important;
            letter-spacing: 0 !important;
        }

        div[data-testid="stVerticalBlock"]:has(#vf-top-nav-anchor) .vf-nav-btn .stButton > button[kind="tertiary"]:hover {
            color: #ffffff !important;
            background: transparent !important;
        }

        div[data-testid="stVerticalBlock"]:has(#vf-top-nav-anchor) .vf-nav-btn .stButton > button[kind="tertiary"]:focus,
        div[data-testid="stVerticalBlock"]:has(#vf-top-nav-anchor) .vf-nav-btn .stButton > button[kind="tertiary"]:focus-visible,
        div[data-testid="stVerticalBlock"]:has(#vf-top-nav-anchor) .vf-nav-btn .stButton > button[kind="tertiary"]:active {
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
            background: transparent !important;
            color: #ffffff !important;
        }

        @media (max-width: 900px) {
            div[data-testid="stVerticalBlock"]:has(#vf-top-nav-anchor) {
                padding: 16px 18px 14px 18px !important;
            }
            .vf-brand {
                font-size: 20px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )



def render_top_nav() -> None:
    with st.container():
        st.markdown('<div id="vf-top-nav-anchor"></div>', unsafe_allow_html=True)
        brand_col, spacer_col, nav1, nav2, nav3, nav4 = st.columns([4.2, 2.0, 1.25, 1.55, 0.95, 1.55], gap="small")

        with brand_col:
            st.markdown('<div class="vf-brand">Viabilidade-Fácil<span>.</span></div>', unsafe_allow_html=True)

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
