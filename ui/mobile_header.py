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
        .vf-mobile-shell-marker,
        .vf-mobile-menu-anchor,
        .vf-mobile-brand-anchor {{
            display: none;
        }}

        @media (max-width: 768px) {{
            [data-testid="stHorizontalBlock"]:has(.vf-brand) {{
                display: none !important;
            }}

            [data-testid="stHorizontalBlock"]:has(.vf-mobile-brand-anchor) {{
                background: {BLUE} !important;
                border-bottom: 3px solid {ORANGE} !important;
                min-height: 72px !important;
                padding: 0.55rem 0.85rem !important;
                margin: 0 0 0.85rem 0 !important;
                border-radius: 0 !important;
                align-items: center !important;
            }}

            [data-testid="stHorizontalBlock"]:has(.vf-mobile-brand-anchor) > div,
            [data-testid="stHorizontalBlock"]:has(.vf-mobile-brand-anchor) [data-testid="stColumn"],
            [data-testid="stHorizontalBlock"]:has(.vf-mobile-brand-anchor) [data-testid="stColumn"] > div {{
                min-height: 60px !important;
                display: flex !important;
                align-items: center !important;
            }}

            [data-testid="stHorizontalBlock"]:has(.vf-mobile-brand-anchor) [data-testid="stColumn"]:first-child > div {{
                justify-content: flex-start !important;
            }}

            [data-testid="stHorizontalBlock"]:has(.vf-mobile-brand-anchor) [data-testid="stColumn"]:last-child > div {{
                justify-content: flex-end !important;
            }}

            .vf-mobile-brand-anchor {{
                display: block !important;
            }}

            .vf-mobile-brand,
            .vf-mobile-brand:hover,
            .vf-mobile-brand:focus,
            .vf-mobile-brand:focus-visible,
            .vf-mobile-brand:active,
            .vf-mobile-brand:visited {{
                color: {WHITE} !important;
                text-decoration: none !important;
                font-size: 24px !important;
                font-weight: 800 !important;
                letter-spacing: -0.02em !important;
                line-height: 1 !important;
                white-space: nowrap !important;
                display: inline-flex !important;
                align-items: center !important;
                min-height: 44px !important;
            }}

            .vf-mobile-brand-dot {{
                color: {ORANGE} !important;
                margin-left: 2px !important;
            }}

            [data-testid="stHorizontalBlock"]:has(.vf-mobile-brand-anchor) .stButton {{
                width: auto !important;
                margin: 0 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: flex-end !important;
            }}

            [data-testid="stHorizontalBlock"]:has(.vf-mobile-brand-anchor) .stButton > button {{
                width: 44px !important;
                min-width: 44px !important;
                height: 44px !important;
                min-height: 44px !important;
                padding: 0 !important;
                border: none !important;
                box-shadow: none !important;
                background: transparent !important;
                color: {WHITE} !important;
                border-radius: 10px !important;
                font-size: 28px !important;
                font-weight: 700 !important;
                line-height: 1 !important;
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
            }}

            [data-testid="stHorizontalBlock"]:has(.vf-mobile-brand-anchor) .stButton > button:hover,
            [data-testid="stHorizontalBlock"]:has(.vf-mobile-brand-anchor) .stButton > button:focus,
            [data-testid="stHorizontalBlock"]:has(.vf-mobile-brand-anchor) .stButton > button:focus-visible,
            [data-testid="stHorizontalBlock"]:has(.vf-mobile-brand-anchor) .stButton > button:active {{
                border: none !important;
                box-shadow: none !important;
                background: rgba(255,255,255,0.08) !important;
                color: {WHITE} !important;
            }}

            [data-testid="stVerticalBlock"]:has(.vf-mobile-menu-anchor) {{
                background: {BLUE} !important;
                border-bottom: 3px solid {ORANGE} !important;
                padding: 0.4rem 0.85rem 0.9rem 0.85rem !important;
                margin: -0.85rem 0 1rem 0 !important;
            }}

            .vf-mobile-menu-anchor {{
                display: block !important;
                width: 100% !important;
                height: 0 !important;
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
                margin: 0 0 0.5rem 0 !important;
                padding: 0 0.8rem !important;
                border-radius: 12px !important;
                background: rgba(255,255,255,0.08) !important;
                color: {WHITE} !important;
                text-decoration: none !important;
                font-size: 14px !important;
                font-weight: 600 !important;
                text-align: center !important;
            }}

            [data-testid="stVerticalBlock"]:has(.vf-mobile-menu-anchor) .stButton {{
                width: 100% !important;
                margin: 0 0 0.5rem 0 !important;
            }}

            [data-testid="stVerticalBlock"]:has(.vf-mobile-menu-anchor) .stButton > button {{
                width: 100% !important;
                min-height: 44px !important;
                border: none !important;
                box-shadow: none !important;
                border-radius: 12px !important;
                background: rgba(255,255,255,0.08) !important;
                color: {WHITE} !important;
                font-size: 14px !important;
                font-weight: 600 !important;
            }}

            [data-testid="stVerticalBlock"]:has(.vf-mobile-menu-anchor) .stButton > button:hover,
            [data-testid="stVerticalBlock"]:has(.vf-mobile-menu-anchor) .stButton > button:focus,
            [data-testid="stVerticalBlock"]:has(.vf-mobile-menu-anchor) .stButton > button:focus-visible,
            [data-testid="stVerticalBlock"]:has(.vf-mobile-menu-anchor) .stButton > button:active {{
                border: none !important;
                box-shadow: none !important;
                background: rgba(255,255,255,0.16) !important;
                color: {WHITE} !important;
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

    cols = st.columns([5.2, 0.8], gap="small")

    with cols[0]:
        home_url = f"{get_app_url()}?nav=home"
        st.markdown(
            f'<div class="vf-mobile-brand-anchor"></div><a class="vf-mobile-brand" href="{home_url}" target="_self" aria-label="Ir para a página inicial do sistema no mobile">Viabilidade-Fácil<span class="vf-mobile-brand-dot">.</span></a>',
            unsafe_allow_html=True,
        )

    with cols[1]:
        if st.button(
            "✕" if st.session_state.get("vf_mobile_nav_open") else "☰",
            key="vf_mobile_nav_toggle",
            help="Abrir menu mobile",
        ):
            st.session_state["vf_mobile_nav_open"] = not st.session_state.get("vf_mobile_nav_open", False)
            st.rerun()

    if st.session_state.get("vf_mobile_nav_open"):
        with st.container():
            st.markdown('<div class="vf-mobile-menu-anchor"></div>', unsafe_allow_html=True)
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
