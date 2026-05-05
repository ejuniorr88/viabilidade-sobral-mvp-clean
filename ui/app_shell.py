from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import streamlit as st
import streamlit.components.v1 as components

from core.auth import get_app_url, safe_get_query_param
from core.credits import get_credit_balance
from core.env_secrets import get_secret_str
from core.state_helpers import clear_all_checkout_states
from ui.auth_panel import render_google_login_box
from ui.mobile_header import inject_mobile_header_styles, render_mobile_top_nav


BLUE = "#071847"
ORANGE = "#d68910"
WHITE = "#ffffff"
TEXT = "#1f2a44"
DEFAULT_LANDING_BASE_URLS = {
    "production": "https://www.viabilidadefacil.com.br",
    "homolog": "https://homolog.viabilidadefacil.com.br",
    "staging": "https://homolog.viabilidadefacil.com.br",
}


def _extract_host_from_header_value(raw: str) -> str:
    value = (raw or "").strip()
    if not value:
        return ""

    parsed = urlparse(value if "://" in value else f"https://{value}")
    return (parsed.hostname or "").lower()


def _get_request_host() -> str:
    candidates: list[str] = []

    try:
        ctx_headers = st.context.headers if hasattr(st, "context") else None
        if ctx_headers:
            for key in ("X-Forwarded-Host", "Host", "Origin", "Referer"):
                raw = ctx_headers.get(key) or ctx_headers.get(key.lower())
                host = _extract_host_from_header_value(raw)
                if host:
                    candidates.append(host)
    except Exception:
        pass

    for host in candidates:
        if host:
            return host

    return ""


def _detect_landing_environment(app_url: str) -> str:
    host = _get_request_host() or (urlparse((app_url or "").strip()).hostname or "").lower()

    if host in {"app.viabilidadefacil.com.br", "www.app.viabilidadefacil.com.br"}:
        return "production"

    if "stable" in host or "homolog" in host or "staging" in host:
        return "homolog"

    if host.endswith(".up.railway.app") or host.endswith(".streamlit.app") or host.endswith(".vercel.app"):
        return "homolog"

    if host in {"localhost", "127.0.0.1"}:
        return "homolog"

    return "production"


def _get_landing_base_url() -> str:
    app_url = (get_app_url() or "").strip()
    environment = _detect_landing_environment(app_url)

    runtime_urls = {
        "production": get_secret_str("LANDING_URL_PRODUCTION", "").strip(),
        "homolog": get_secret_str("LANDING_URL_HOMOLOG", "").strip(),
        "staging": get_secret_str("LANDING_URL_STAGING", "").strip(),
    }
    legacy_fallback = get_secret_str("LANDING_BASE_URL", "").strip()

    base_url = runtime_urls.get(environment) or legacy_fallback or DEFAULT_LANDING_BASE_URLS[environment]
    return base_url.rstrip("/")


def _build_landing_url(path: str) -> str:
    return f"{_get_landing_base_url()}/{path.lstrip('/')}"


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


def _return_to_study_from_header() -> None:
    """Return to the study with the same reset used by the working back action.

    This intentionally does not touch authentication/session keys.
    """
    st.session_state["show_client_area"] = False
    st.session_state["show_plans_page"] = False
    st.session_state["post_login_action"] = None
    clear_all_checkout_states()


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

        .vf-brand-anchor {{
            display: none !important;
        }}

        [data-testid="stHorizontalBlock"]:has(.vf-brand) > div:first-child {{
            position: relative !important;
        }}

        [data-testid="stHorizontalBlock"]:has(.vf-brand) > div:first-child .stButton {{
            justify-content: flex-start !important;
            position: static !important;
            z-index: 30 !important;
            width: auto !important;
            min-width: 0 !important;
            margin: 0 !important;
        }}

        [data-testid="stHorizontalBlock"]:has(.vf-brand) > div:first-child .stButton > button[kind="tertiary"] {{
            opacity: 1 !important;
            width: auto !important;
            min-width: 0 !important;
            height: 92px !important;
            min-height: 92px !important;
            margin: 0 !important;
            padding: 0 !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: {WHITE} !important;
            font-size: 30px !important;
            font-weight: 800 !important;
            letter-spacing: -0.02em !important;
            justify-content: flex-start !important;
            text-align: left !important;
        }}

        [data-testid="stHorizontalBlock"]:has(.vf-brand) > div:first-child .stButton > button[kind="tertiary"] p,
        [data-testid="stHorizontalBlock"]:has(.vf-brand) > div:first-child .stButton > button[kind="tertiary"] span,
        [data-testid="stHorizontalBlock"]:has(.vf-brand) > div:first-child .stButton > button[kind="tertiary"] div {{
            color: {WHITE} !important;
            font-size: 30px !important;
            font-weight: 800 !important;
            letter-spacing: -0.02em !important;
            line-height: 1 !important;
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
            cursor: pointer;
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

        /* Keep the real Streamlit logo button anchored to the left.
           The generic nav button rule above centers menu buttons; this scoped
           override preserves the working click behavior and restores the
           original brand position. */
        [data-testid="stHorizontalBlock"]:has(.vf-brand) > div:first-child .stButton {{
            width: auto !important;
            justify-content: flex-start !important;
        }}

        [data-testid="stHorizontalBlock"]:has(.vf-brand) > div:first-child .stButton > button[kind="tertiary"] {{
            width: auto !important;
            justify-content: flex-start !important;
            text-align: left !important;
        }}

        [data-testid="stHorizontalBlock"]:has(.vf-brand) .vf-nav-link-wrap,
        [data-testid="stHorizontalBlock"]:has(.vf-brand) .vf-nav-link-wrap > div,
        [data-testid="stHorizontalBlock"]:has(.vf-brand) .vf-nav-link-wrap p {{
            margin: 0 !important;
            width: 100% !important;
            min-height: 92px !important;
        }}

        [data-testid="stHorizontalBlock"]:has(.vf-brand) .vf-nav-link-button {{
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
            cursor: pointer !important;
            position: relative !important;
            z-index: 20 !important;
            transition: background 0.18s ease, opacity 0.18s ease !important;
            display: flex !important;
            text-decoration: none !important;
            text-align: center !important;
        }}

        [data-testid="stHorizontalBlock"]:has(.vf-brand) .vf-nav-link-button:hover {{
            color: {WHITE} !important;
            background: rgba(255,255,255,0.14) !important;
            opacity: 1 !important;
        }}

        [data-testid="stHorizontalBlock"]:has(.vf-brand) .vf-nav-link-button:focus,
        [data-testid="stHorizontalBlock"]:has(.vf-brand) .vf-nav-link-button:focus-visible,
        [data-testid="stHorizontalBlock"]:has(.vf-brand) .vf-nav-link-button:active {{
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
            background: rgba(255,255,255,0.12) !important;
            color: {WHITE} !important;
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


        /* Sidebar legibility: visual-only adjustment scoped to Streamlit sidebar. */
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] .stMarkdown p {{
            font-size: 13px !important;
            line-height: 1.45 !important;
        }}

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {{
            font-size: 16px !important;
            font-weight: 700 !important;
            line-height: 1.25 !important;
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
            [data-testid="stHorizontalBlock"]:has(.vf-brand) .stButton > button[kind="tertiary"],
            [data-testid="stHorizontalBlock"]:has(.vf-brand) .vf-nav-link-wrap,
            [data-testid="stHorizontalBlock"]:has(.vf-brand) .vf-nav-link-wrap > div,
            [data-testid="stHorizontalBlock"]:has(.vf-brand) .vf-nav-link-button {{
                font-size: 13px !important;
                min-height: 76px !important;
            }}
        }}
        </style>
        ''',
        unsafe_allow_html=True,
    )


def render_top_nav() -> None:
    cols = st.columns([2.35, 2.55, 1.35, 1.55, 0.95, 1.6], gap="small")

    with cols[0]:
        # Hidden marker only to keep the scoped header CSS active.
        # The visible logo is the real Streamlit button below.
        st.markdown('<span class="vf-brand vf-brand-anchor" aria-hidden="true"></span>', unsafe_allow_html=True)
        if st.button("Viabilidade-Fácil.", key="vf_nav_home", type="tertiary", use_container_width=False):
            _return_to_study_from_header()
            st.rerun()

    with cols[2]:
        st.markdown(
            f'<div class="vf-nav-link-wrap"><a id="vf_nav_how" class="vf-nav-link-button" href="{_build_landing_url("entenda-o-sistema.html")}" target="_self" aria-label="Abrir página Como funciona na mesma aba">Como funciona</a></div>',
            unsafe_allow_html=True,
        )

    with cols[3]:
        if st.button("Área do cliente", key="vf_nav_client", type="tertiary", use_container_width=True):
            st.session_state["show_client_area"] = True
            st.session_state["show_plans_page"] = False
            if not st.session_state.get("auth_logged_in"):
                st.session_state["post_login_action"] = "open_client_area"
            st.rerun()

    with cols[4]:
        st.markdown(
            f'<div class="vf-nav-link-wrap"><a id="vf_nav_plans" class="vf-nav-link-button" href="{_build_landing_url("planos.html")}" target="_self" aria-label="Abrir página de planos na mesma aba">Planos</a></div>',
            unsafe_allow_html=True,
        )

    with cols[5]:
        st.markdown(
            f'<div class="vf-nav-link-wrap"><a id="vf_nav_support" class="vf-nav-link-button" href="{_build_landing_url("duvidas-suporte.html")}" target="_self" aria-label="Abrir página de dúvidas e suporte na mesma aba">Dúvidas/Suporte</a></div>',
            unsafe_allow_html=True,
        )

    # ---------------------------------------------------------------------
    # Mobile header
    # Inject scoped styles and render a separate navigation bar on small screens.
    # ---------------------------------------------------------------------
    inject_mobile_header_styles()

    def _on_open_client_area() -> None:
        st.session_state["show_client_area"] = True
        st.session_state["show_plans_page"] = False
        if not st.session_state.get("auth_logged_in"):
            st.session_state["post_login_action"] = "open_client_area"
        st.rerun()

    _brand_home_url = "?nav=home"
    _how_url = _build_landing_url("entenda-o-sistema.html")
    _plans_url = _build_landing_url("planos.html")
    _support_url = _build_landing_url("duvidas-suporte.html")

    render_mobile_top_nav(
        brand="Viabilidade-Fácil",
        home_url=_brand_home_url,
        how_url=_how_url,
        plans_url=_plans_url,
        support_url=_support_url,
        on_open_client_area=_on_open_client_area,
    )

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
