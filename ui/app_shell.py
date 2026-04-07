from __future__ import annotations

from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from core.auth import get_app_url, safe_get_query_param
from core.credits import get_credit_balance
from ui.auth_panel import render_google_login_box


SITE_HEADER_BG = "#0b132b"
SITE_HEADER_ACCENT = "#f59e0b"


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
        f"""
        <style>
        .block-container {{
            padding-top: 0.45rem !important;
            padding-bottom: 2rem !important;
            max-width: 100% !important;
        }}

        html, body, [data-testid="stAppViewContainer"], .main {{
            overflow-x: hidden !important;
        }}

        header[data-testid="stHeader"] {{
            background: transparent !important;
        }}

        .vf-brand {{
            font-size: 2rem;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: -0.02em;
            line-height: 1.1;
            white-space: nowrap;
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }}

        .vf-brand-accent {{
            color: {SITE_HEADER_ACCENT};
        }}

        .vf-topbar-anchor + div[data-testid="stHorizontalBlock"] {{
            background: {SITE_HEADER_BG};
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 1.05rem 1.35rem;
            margin: 0 0 1.35rem 0;
            align-items: center;
            box-shadow: 0 10px 28px rgba(11, 19, 43, 0.08);
        }}

        .vf-topbar-anchor + div[data-testid="stHorizontalBlock"] [data-testid="column"] {{
            display: flex;
            align-items: center;
        }}

        .vf-topbar-anchor + div[data-testid="stHorizontalBlock"] .stButton > button {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: rgba(255,255,255,0.88) !important;
            font-size: 0.88rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.06em !important;
            text-transform: uppercase !important;
            padding: 0 !important;
            min-height: auto !important;
            line-height: 1.15 !important;
            justify-content: flex-end !important;
        }}

        .vf-topbar-anchor + div[data-testid="stHorizontalBlock"] .stButton > button:hover {{
            color: #ffffff !important;
            background: transparent !important;
        }}

        .vf-topbar-anchor + div[data-testid="stHorizontalBlock"] .stButton > button:focus,
        .vf-topbar-anchor + div[data-testid="stHorizontalBlock"] .stButton > button:focus-visible,
        .vf-topbar-anchor + div[data-testid="stHorizontalBlock"] .stButton > button:active {{
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
            background: transparent !important;
        }}

        @media (max-width: 1100px) {{
            .vf-brand {{
                font-size: 1.7rem;
            }}
            .vf-topbar-anchor + div[data-testid="stHorizontalBlock"] .stButton > button {{
                font-size: 0.78rem !important;
                letter-spacing: 0.04em !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )



def render_top_nav() -> None:
    st.markdown('<div class="vf-topbar-anchor"></div>', unsafe_allow_html=True)
    brand_col, nav1, nav2, nav3, nav4 = st.columns([4.3, 1.3, 1.8, 1.0, 1.8], gap="medium")

    with brand_col:
        st.markdown(
            '<div class="vf-brand">Viabilidade-Fácil<span class="vf-brand-accent">.</span></div>',
            unsafe_allow_html=True,
        )

    with nav1:
        st.button("Como funciona", key="vf_nav_how", type="tertiary", use_container_width=False)

    with nav2:
        if st.button("Área do cliente", key="vf_nav_client", type="tertiary", use_container_width=False):
            st.session_state["show_client_area"] = True
            if not st.session_state.get("auth_logged_in"):
                st.session_state["post_login_action"] = "open_client_area"
            st.rerun()

    with nav3:
        st.button("Planos", key="vf_nav_plans", type="tertiary", use_container_width=False)

    with nav4:
        st.button("Dúvida e suporte", key="vf_nav_support", type="tertiary", use_container_width=False)



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
