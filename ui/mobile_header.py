from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from core.auth import get_app_url


BLUE = "#071847"
ORANGE = "#d68910"
WHITE = "#ffffff"


def inject_mobile_header_styles() -> None:
    st.markdown(
        f'''
        <style>
        .vf-mobile-shell,
        .vf-mobile-menu-panel {{
            display: none;
        }}

        @media (max-width: 768px) {{
            [data-testid="stHorizontalBlock"]:has(.vf-brand) {{
                display: none !important;
            }}

            .vf-mobile-shell,
            .vf-mobile-menu-panel {{
                display: block !important;
            }}

            [data-testid="stHorizontalBlock"]:has(.vf-mobile-brand) {{
                background: {BLUE} !important;
                border-bottom: 3px solid {ORANGE} !important;
                min-height: 72px !important;
                padding: 0.45rem 0.8rem !important;
                margin: 0 0 0.7rem 0 !important;
                border-radius: 0 !important;
                align-items: center !important;
            }}

            [data-testid="stHorizontalBlock"]:has(.vf-mobile-brand) > div,
            [data-testid="stHorizontalBlock"]:has(.vf-mobile-brand) [data-testid="stColumn"],
            [data-testid="stHorizontalBlock"]:has(.vf-mobile-brand) [data-testid="stColumn"] > div {{
                min-height: 60px !important;
                align-items: center !important;
            }}

            .vf-mobile-brand,
            .vf-mobile-brand:hover,
            .vf-mobile-brand:focus,
            .vf-mobile-brand:focus-visible,
            .vf-mobile-brand:active,
            .vf-mobile-brand:visited {{
                color: {WHITE} !important;
                text-decoration: none !important;
                font-size: 18px !important;
                font-weight: 800 !important;
                letter-spacing: -0.02em !important;
                line-height: 1 !important;
                white-space: nowrap !important;
            }}

            .vf-mobile-brand-dot {{
                color: {ORANGE} !important;
                margin-left: 2px !important;
            }}

            [data-testid="stHorizontalBlock"]:has(.vf-mobile-brand) .stButton {{
                width: 100% !important;
                display: flex !important;
                justify-content: flex-end !important;
                align-items: center !important;
            }}

            [data-testid="stHorizontalBlock"]:has(.vf-mobile-brand) .stButton > button {{
                min-height: 48px !important;
                padding: 0 1rem !important;
                border-radius: 999px !important;
                border: none !important;
                box-shadow: none !important;
                background: rgba(255,255,255,0.14) !important;
                color: {WHITE} !important;
                font-size: 14px !important;
                font-weight: 700 !important;
            }}

            [data-testid="stHorizontalBlock"]:has(.vf-mobile-brand) .stButton > button:hover,
            [data-testid="stHorizontalBlock"]:has(.vf-mobile-brand) .stButton > button:focus,
            [data-testid="stHorizontalBlock"]:has(.vf-mobile-brand) .stButton > button:focus-visible,
            [data-testid="stHorizontalBlock"]:has(.vf-mobile-brand) .stButton > button:active {{
                border: none !important;
                box-shadow: none !important;
                background: rgba(255,255,255,0.20) !important;
                color: {WHITE} !important;
            }}

            [data-testid="stVerticalBlock"]:has(.vf-mobile-menu-panel) {{
                background: {BLUE} !important;
                border-bottom: 3px solid {ORANGE} !important;
                padding: 0.4rem 0.8rem 0.85rem 0.8rem !important;
                margin: -0.7rem 0 0.9rem 0 !important;
            }}

            .vf-mobile-link,
            .vf-mobile-link:hover,
            .vf-mobile-link:focus,
            .vf-mobile-link:focus-visible,
            .vf-mobile-link:active,
            .vf-mobile-link:visited {{
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                min-height: 44px !important;
                margin: 0 0 0.45rem 0 !important;
                padding: 0 0.8rem !important;
                border-radius: 10px !important;
                background: rgba(255,255,255,0.08) !important;
                color: {WHITE} !important;
                text-decoration: none !important;
                font-size: 14px !important;
                font-weight: 600 !important;
                text-align: center !important;
            }}

            .vf-mobile-link:last-child {{
                margin-bottom: 0 !important;
            }}
        }}
        </style>
        ''',
        unsafe_allow_html=True,
    )


def render_mobile_top_nav(
    *,
    build_landing_url: Callable[[str], str],
    on_open_client_area: Callable[[], None],
) -> None:
    st.session_state.setdefault("vf_mobile_nav_open", False)

    cols = st.columns([4.2, 1.3], gap="small")

    with cols[0]:
        home_url = f"{get_app_url()}?nav=home"
        st.markdown(
            f'<div class="vf-mobile-shell"></div><a class="vf-mobile-brand" href="{home_url}" target="_self" aria-label="Ir para a página inicial do sistema no mobile">Viabilidade-Fácil<span class="vf-mobile-brand-dot">.</span></a>',
            unsafe_allow_html=True,
        )

    with cols[1]:
        if st.button(
            "Fechar" if st.session_state.get("vf_mobile_nav_open") else "Menu",
            key="vf_mobile_nav_toggle",
            use_container_width=True,
        ):
            st.session_state["vf_mobile_nav_open"] = not st.session_state.get("vf_mobile_nav_open", False)
            st.rerun()

    if st.session_state.get("vf_mobile_nav_open"):
        st.markdown('<div class="vf-mobile-menu-panel"></div>', unsafe_allow_html=True)
        st.markdown(
            f'''
            <a class="vf-mobile-link" href="{build_landing_url("entenda-o-sistema.html")}" target="_self" aria-label="Abrir página Como funciona na mesma aba no mobile">Como funciona</a>
            ''',
            unsafe_allow_html=True,
        )
        if st.button("Área do cliente", key="vf_mobile_nav_client", use_container_width=True):
            st.session_state["vf_mobile_nav_open"] = False
            on_open_client_area()
        st.markdown(
            f'''
            <a class="vf-mobile-link" href="{build_landing_url("planos.html")}" target="_self" aria-label="Abrir página de planos na mesma aba no mobile">Planos</a>
            <a class="vf-mobile-link" href="{build_landing_url("duvidas-suporte.html")}" target="_self" aria-label="Abrir página de dúvidas e suporte na mesma aba no mobile">Dúvidas/Suporte</a>
            ''',
            unsafe_allow_html=True,
        )
