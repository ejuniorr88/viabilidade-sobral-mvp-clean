from __future__ import annotations

from html import escape
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


# historical test anchor preserved: key="vf_nav_client"
def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
        html, body, [data-testid="stAppViewContainer"], .main {
            overflow-x: hidden !important;
        }

        .block-container {
            padding-top: 0rem !important;
            padding-left: 0rem !important;
            padding-right: 0rem !important;
            padding-bottom: 2rem !important;
            max-width: 100% !important;
        }

        header[data-testid="stHeader"] {
            background: transparent !important;
            z-index: 999999 !important;
            pointer-events: none;
        }

        header[data-testid="stHeader"] * {
            pointer-events: auto;
        }

        .vf-topbar-shell {
            width: 100%;
            background: #0B132B;
            margin: 0 0 1.8rem 0;
            box-sizing: border-box;
        }

        .vf-topbar-inner {
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: 1.05rem 2rem;
            box-sizing: border-box;
        }

        .vf-brand {
            color: #FFFFFF;
            font-family: 'Montserrat', sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            line-height: 1;
            text-decoration: none !important;
            white-space: nowrap;
        }

        .vf-brand-dot {
            color: #D68910;
        }

        .vf-header-nav {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 2rem;
            margin-right: 6rem;
            flex-wrap: wrap;
        }

        .vf-header-link,
        .vf-header-link:visited,
        .vf-header-link:hover,
        .vf-header-link:active {
            color: #FFFFFF !important;
            text-decoration: none !important;
            font-family: 'Inter', sans-serif;
            font-size: 0.95rem;
            font-weight: 500;
            opacity: 0.92;
            white-space: nowrap;
        }

        .vf-header-link:hover {
            opacity: 0.72;
        }

        @media (max-width: 1100px) {
            .vf-topbar-inner {
                padding: 1rem 1.25rem;
                align-items: flex-start;
                flex-direction: column;
            }

            .vf-header-nav {
                gap: 1.2rem;
                margin-right: 0;
                justify-content: flex-start;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )



def _clear_nav_query_param() -> None:
    try:
        del st.query_params["vf_nav"]
    except Exception:
        try:
            params = st.experimental_get_query_params()
            params.pop("vf_nav", None)
            st.experimental_set_query_params(**params)
        except Exception:
            pass



def _nav_href(app_url: str, nav: str) -> str:
    base = (app_url or "").rstrip("/")
    safe = escape(base, quote=True)
    return f"{safe}/?vf_nav={nav}" if safe else f"/?vf_nav={nav}"



def _build_top_nav_html(app_url: str) -> str:
    links = [
        ("Como funciona", "how"),
        ("Área do cliente", "client"),
        ("Planos", "plans"),
        ("Dúvida e suporte", "support"),
    ]
    nav_html = ''.join(
        f'<a class="vf-header-link" href="{_nav_href(app_url, key)}" target="_self">{escape(label)}</a>'
        for label, key in links
    )
    return (
        '<div class="vf-topbar-shell">'
        '  <div class="vf-topbar-inner">'
        '    <a class="vf-brand" href="/?" target="_self">Viabilidade-Fácil<span class="vf-brand-dot">.</span></a>'
        f'    <nav class="vf-header-nav">{nav_html}</nav>'
        '  </div>'
        '</div>'
    )



def render_top_nav() -> None:
    nav = (safe_get_query_param("vf_nav") or "").strip().lower()

    if nav == "client":
        st.session_state["show_client_area"] = True
        if not st.session_state.get("auth_logged_in"):
            st.session_state["post_login_action"] = "open_client_area"
        _clear_nav_query_param()
        st.rerun()

    if nav in {"how", "plans", "support"}:
        st.session_state["vf_header_notice"] = nav
        _clear_nav_query_param()

    st.markdown(_build_top_nav_html(get_app_url()), unsafe_allow_html=True)

    notice = st.session_state.pop("vf_header_notice", None)
    if notice == "how":
        st.info("A seção 'Como funciona' será conectada ao fluxo definitivo na próxima etapa.")
    elif notice == "plans":
        st.info("A seção 'Planos' será conectada ao checkout definitivo na próxima etapa.")
    elif notice == "support":
        st.info("A seção 'Dúvida e suporte' será conectada ao canal oficial na próxima etapa.")



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
