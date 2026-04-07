from __future__ import annotations

from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from core.auth import get_app_url, safe_get_query_param
from ui.header_bar import build_header_bar_html
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
            padding-top: 0.55rem !important;
            padding-bottom: 2rem !important;
            max-width: 100% !important;
        }

        html, body, [data-testid="stAppViewContainer"], .main {
            overflow-x: hidden !important;
        }

        header[data-testid="stHeader"] {
            background: transparent !important;
        }

        .vf-header-wrap {
            width: calc(100% + 2rem);
            margin: 0 -1rem 1rem -1rem;
        }

        .vf-header-bar {
            width: 100%;
            background: #0b1f4d;
            border-radius: 18px;
            min-height: 72px;
            padding: 1rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1.2rem;
            box-sizing: border-box;
        }

        .vf-header-brand {
            color: #ffffff;
            font-size: 1.7rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            line-height: 1;
            white-space: nowrap;
        }

        .vf-header-brand span {
            color: #ff7a00;
        }

        .vf-header-links {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 1.5rem;
            flex-wrap: wrap;
        }

        .vf-header-link, .vf-header-link:visited, .vf-header-link:hover, .vf-header-link:active {
            color: #ffffff !important;
            text-decoration: none !important;
            font-size: 0.98rem;
            font-weight: 600;
            line-height: 1.2;
            white-space: nowrap;
        }

        .vf-header-link:hover {
            opacity: 0.88;
        }

        @media (max-width: 980px) {
            .vf-header-bar {
                padding: 0.95rem 1.1rem;
                align-items: flex-start;
                flex-direction: column;
            }

            .vf-header-brand {
                font-size: 1.45rem;
            }

            .vf-header-links {
                width: 100%;
                justify-content: flex-start;
                gap: 1rem;
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

    st.markdown(build_header_bar_html(get_app_url()), unsafe_allow_html=True)

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
