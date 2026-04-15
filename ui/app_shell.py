from __future__ import annotations

from typing import Any

import streamlit as st

from core.auth import get_app_url, safe_get_query_param
from core.credits import get_credit_balance
from ui.auth_panel import render_google_login_box


BLUE = "#071847"
ORANGE = "#d68910"
WHITE = "#ffffff"
TEXT = "#1f2a44"


def card(title: str, value: Any, suffix: str = "") -> None:
    rendered = "—" if value is None or value == "" else f"{value}{suffix}"
    st.markdown(
        f'''
        <div style="padding:12px;border:1px solid #e7e7e7;border-radius:12px;margin-bottom:10px;background:#fff;">
            <div style="font-size:12px;opacity:.75">{title}</div>
            <div style="font-size:20px;font-weight:700">{rendered}</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def inject_global_styles() -> None:
    st.markdown(
        f'''
        <style>
        .block-container {{
            padding-top: 0.35rem !important;
            padding-bottom: 2rem !important;
            max-width: 100% !important;
        }}

        html, body, [data-testid="stAppViewContainer"], .main {{
            overflow-x: hidden !important;
        }}

        [data-testid="stAppViewContainer"] {{
            background: #ffffff !important;
        }}

        header[data-testid="stHeader"] {{
            background: transparent !important;
            z-index: 999999 !important;
            pointer-events: none !important;
        }}

        header[data-testid="stHeader"] * {{
            pointer-events: auto !important;
        }}

        div[data-testid="stToolbar"] {{
            pointer-events: none !important;
        }}

        div[data-testid="stToolbar"] button,
        div[data-testid="stToolbar"] a,
        div[data-testid="stToolbar"] [role="button"] {{
            pointer-events: auto !important;
        }}

        [data-testid="stHorizontalBlock"]:has(.vf-brand) {{
            background: {BLUE} !important;
            border-bottom: 3px solid {ORANGE} !important;
            min-height: 92px;
            padding: 0 1.4rem !important;
            margin-bottom: 1.25rem !important;
            border-radius: 0 !important;
            align-items: center !important;
            position: relative !important;
            z-index: 10 !important;
        }}

        [data-testid="stHorizontalBlock"]:has(.vf-brand) > div {{
            display: flex !important;
            align-items: center !important;
            min-height: 92px !important;
        }}

        [data-testid="stHorizontalBlock"]:has(.vf-brand) > div:first-child {{
            justify-content: flex-start !important;
        }}

        [data-testid="stHorizontalBlock"]:has(.vf-brand) [data-testid="stColumn"] {{
            display: flex !important;
            align-items: center !important;
            min-height: 92px !important;
        }}

        [data-testid="stHorizontalBlock"]:has(.vf-brand) [data-testid="stColumn"] > div {{
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            min-height: 92px !important;
        }}

        .vf-brand-home {{
            display: inline-flex;
            align-items: center;
            min-height: 92px;
            text-decoration: none !important;
            color: inherit !important;
            cursor: pointer;
        }}

        .vf-brand-home:hover,
        .vf-brand-home:focus,
        .vf-brand-home:focus-visible,
        .vf-brand-home:active,
        .vf-brand-home:visited {{
            text-decoration: none !important;
            color: inherit !important;
            outline: none !important;
        }}

        .vf-brand {{
            font-size: 30px;
            font-weight: 800;
            color: {WHITE};
            letter-spacing: -0.02em;
            line-height: 1;
            white-space: nowrap;
            margin: 0;
            min-height: 92px;
            display: flex;
            align-items: center;
            font-family: inherit !important;
        }}

        .vf-brand-dot {{
            color: {ORANGE};
            margin-left: 2px;
        }}

        [data-testid="stHorizontalBlock"]:has(.vf-brand) .stButton {{
            width: 100%;
            margin: 0;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            min-height: 92px !important;
        }}

        [data-testid="stHorizontalBlock"]:has(.vf-brand) .stButton > button[kind="tertiary"] {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: {WHITE} !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            white-space: nowrap !important;
            padding: 0 12px !important;
            min-height: 92px !important;
            line-height: 1 !important;
            justify-content: center !important;
            align-items: center !important;
            width: 100% !important;
            border-radius: 8px !important;
            margin: 0 !important;
            pointer-events: auto !important;
            cursor: pointer !important;
            position: relative !important;
            z-index: 20 !important;
            transition: background 0.18s ease, opacity 0.18s ease !important;
            display: flex !important;
        }}

        [data-testid="stHorizontalBlock"]:has(.vf-brand) .stButton > button[kind="tertiary"] p,
        [data-testid="stHorizontalBlock"]:has(.vf-brand) .stButton > button[kind="tertiary"] span,
        [data-testid="stHorizontalBlock"]:has(.vf-brand) .stButton > button[kind="tertiary"] div {{
            pointer-events: none !important;
            background: transparent !important;
        }}

        [data-testid="stHorizontalBlock"]:has(.vf-brand) .stButton > button[kind="tertiary"]:hover {{
            color: {WHITE} !important;
            background: rgba(255,255,255,0.14) !important;
            opacity: 1 !important;
        }}

        [data-testid="stHorizontalBlock"]:has(.vf-brand) .stButton > button[kind="tertiary"]:focus,
        [data-testid="stHorizontalBlock"]:has(.vf-brand) .stButton > button[kind="tertiary"]:focus-visible,
        [data-testid="stHorizontalBlock"]:has(.vf-brand) .stButton > button[kind="tertiary"]:active {{
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
            background: rgba(255,255,255,0.12) !important;
            color: {WHITE} !important;
        }}

        @media (max-width: 900px) {{
            [data-testid="stHorizontalBlock"]:has(.vf-brand) {{
                min-height: 76px;
                padding: 0 0.9rem !important;
            }}

            [data-testid="stHorizontalBlock"]:has(.vf-brand) > div,
            [data-testid="stHorizontalBlock"]:has(.vf-brand) [data-testid="stColumn"],
            [data-testid="stHorizontalBlock"]:has(.vf-brand) [data-testid="stColumn"] > div {{
                min-height: 76px !important;
            }}

            .vf-brand {{
                font-size: 24px;
                min-height: 76px;
            }}

            [data-testid="stHorizontalBlock"]:has(.vf-brand) .stButton,
            [data-testid="stHorizontalBlock"]:has(.vf-brand) .stButton > button[kind="tertiary"] {{
                font-size: 13px !important;
                min-height: 76px !important;
            }}
        }}
        </style>
        ''',
        unsafe_allow_html=True,
    )


def render_top_nav() -> None:
    cols = st.columns([3.8, 1.1, 1.35, 1.55, 0.95, 1.6], gap="small")

    with cols[0]:
        home_url = get_app_url()
        st.markdown(
            f'<a class="vf-brand-home" href="{home_url}" target="_self"><div class="vf-brand">Viabilidade-Fácil<span class="vf-brand-dot">.</span></div></a>',
            unsafe_allow_html=True,
        )

    with cols[2]:
        st.button("Como funciona", key="vf_nav_how", type="tertiary", use_container_width=True)

    with cols[3]:
        if st.button("Área do cliente", key="vf_nav_client", type="tertiary", use_container_width=True):
            st.session_state["show_client_area"] = True
            st.session_state["show_plans_page"] = False
            if not st.session_state.get("auth_logged_in"):
                st.session_state["post_login_action"] = "open_client_area"
            st.rerun()

    with cols[4]:
        if st.button("Planos", key="vf_nav_plans", type="tertiary", use_container_width=True):
            st.session_state["show_plans_page"] = True
            st.session_state["show_client_area"] = False
            if not st.session_state.get("auth_logged_in"):
                st.session_state["post_login_action"] = "open_plans_page"
            st.rerun()

    with cols[5]:
        st.button("Dúvidas/Suporte", key="vf_nav_support", type="tertiary", use_container_width=True)


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

    bridge_html = f'''
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
    '''

    components.html(bridge_html, height=0)
    st.stop()
