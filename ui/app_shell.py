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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Montserrat:wght@600;700;800&display=swap');

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

        .vf-header-wrap {
            margin-left: calc(-1 * var(--vf-block-pad-left, 1rem));
            margin-right: calc(-1 * var(--vf-block-pad-right, 1rem));
            margin-bottom: 1rem;
        }

        .vf-header-bar {
            width: 100%;
            min-height: 76px;
            background: #0B132B;
            border-radius: 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1.5rem;
            padding: 18px 32px;
            box-sizing: border-box;
        }

        .vf-brand, .vf-brand * {
            font-family: 'Montserrat', sans-serif !important;
        }

        .vf-brand-text {
            color: #FFFFFF;
            font-size: 1.55rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            line-height: 1;
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
            flex-wrap: wrap;
        }

        .vf-header-link {
            color: #FFFFFF !important;
            text-decoration: none !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.95rem;
            font-weight: 500;
            line-height: 1;
            white-space: nowrap;
            opacity: 0.96;
            transition: opacity 0.2s ease, color 0.2s ease;
        }

        .vf-header-link:hover,
        .vf-header-link:focus,
        .vf-header-link:active,
        .vf-header-link:visited {
            color: #FFFFFF !important;
            text-decoration: none !important;
            opacity: 0.78;
        }

        @media (max-width: 1050px) {
            .vf-header-bar {
                padding: 16px 20px;
                gap: 1rem;
            }
            .vf-header-nav {
                gap: 1.2rem;
            }
        }

        @media (max-width: 820px) {
            .vf-header-bar {
                align-items: flex-start;
                flex-direction: column;
            }
            .vf-header-nav {
                justify-content: flex-start;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    components.html(
        """
        <script>
        (function() {
          const parentWindow = window.parent;
          const doc = parentWindow.document;
          const root = doc.documentElement;

          function syncVars() {
            const block = doc.querySelector('.main .block-container');
            if (!block) return;
            const styles = parentWindow.getComputedStyle(block);
            root.style.setProperty('--vf-block-pad-left', styles.paddingLeft || '1rem');
            root.style.setProperty('--vf-block-pad-right', styles.paddingRight || '1rem');
          }

          syncVars();
          parentWindow.addEventListener('resize', syncVars);
          if (parentWindow.ResizeObserver) {
            const observer = new parentWindow.ResizeObserver(syncVars);
            const block = doc.querySelector('.main .block-container');
            if (block) observer.observe(block);
          }
          setTimeout(syncVars, 50);
          setTimeout(syncVars, 250);
        })();
        </script>
        """,
        height=0,
    )



def _consume_header_nav() -> str | None:
    nav = safe_get_query_param("vf_nav") or None
    if not nav:
        return None

    # legado do contrato de fluxo: key="vf_nav_client"
    if nav == "client":
        st.session_state["show_client_area"] = True
        if not st.session_state.get("auth_logged_in"):
            st.session_state["post_login_action"] = "open_client_area"
    elif nav == "how":
        st.session_state["vf_header_notice"] = "A seção 'Como funciona' será conectada em seguida."
    elif nav == "plans":
        st.session_state["vf_header_notice"] = "A seção 'Planos' será conectada em seguida."
    elif nav == "support":
        st.session_state["vf_header_notice"] = "A seção 'Dúvida e suporte' será conectada em seguida."

    try:
        del st.query_params["vf_nav"]
    except Exception:
        pass

    return nav


def render_top_nav() -> None:
    _consume_header_nav()
    st.markdown(build_header_bar_html(get_app_url()), unsafe_allow_html=True)
    notice = st.session_state.pop("vf_header_notice", None)
    if notice:
        st.info(notice)


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
