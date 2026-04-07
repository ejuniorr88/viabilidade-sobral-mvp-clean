from __future__ import annotations

import streamlit as st


def inject_header_bar_styles() -> None:
    st.markdown(
        """
        <style>
        div[data-testid="stVerticalBlock"]:has(#vf-header-anchor) {
            background: #0b2463 !important;
            border-radius: 18px !important;
            padding: 1.05rem 1.4rem 1.0rem 1.4rem !important;
            margin: 0 0 1.15rem 0 !important;
            overflow: hidden !important;
        }

        div[data-testid="stVerticalBlock"]:has(#vf-header-anchor) [data-testid="column"] {
            display: flex !important;
            align-items: center !important;
        }

        div[data-testid="stVerticalBlock"]:has(#vf-header-anchor) .vf-header-brand {
            color: #ffffff !important;
            font-size: 2.05rem !important;
            font-weight: 800 !important;
            letter-spacing: -0.03em !important;
            line-height: 1 !important;
            white-space: nowrap !important;
            margin: 0.05rem 0 0.1rem 0 !important;
        }

        div[data-testid="stVerticalBlock"]:has(#vf-header-anchor) .vf-header-brand .vf-header-dot {
            color: #ff9f1a !important;
        }

        div[data-testid="stVerticalBlock"]:has(#vf-header-anchor) .vf-header-nav .stButton {
            width: 100% !important;
        }

        div[data-testid="stVerticalBlock"]:has(#vf-header-anchor) .vf-header-nav .stButton > button {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #ffffff !important;
            font-size: 0.98rem !important;
            font-weight: 500 !important;
            min-height: auto !important;
            padding: 0.15rem 0 !important;
            line-height: 1.15 !important;
            white-space: nowrap !important;
            justify-content: center !important;
        }

        div[data-testid="stVerticalBlock"]:has(#vf-header-anchor) .vf-header-nav .stButton > button:hover,
        div[data-testid="stVerticalBlock"]:has(#vf-header-anchor) .vf-header-nav .stButton > button:focus,
        div[data-testid="stVerticalBlock"]:has(#vf-header-anchor) .vf-header-nav .stButton > button:focus-visible,
        div[data-testid="stVerticalBlock"]:has(#vf-header-anchor) .vf-header-nav .stButton > button:active {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
            color: #ffffff !important;
        }

        div[data-testid="stVerticalBlock"]:has(#vf-header-anchor) .vf-header-nav .stButton > button p {
            color: #ffffff !important;
            font-size: 0.98rem !important;
            font-weight: 500 !important;
        }

        div[data-testid="stVerticalBlock"]:has(#vf-header-anchor) .vf-header-nav--muted .stButton > button,
        div[data-testid="stVerticalBlock"]:has(#vf-header-anchor) .vf-header-nav--muted .stButton > button p {
            opacity: 0.96 !important;
        }

        @media (max-width: 980px) {
            div[data-testid="stVerticalBlock"]:has(#vf-header-anchor) {
                padding: 0.95rem 1.05rem !important;
            }

            div[data-testid="stVerticalBlock"]:has(#vf-header-anchor) .vf-header-brand {
                font-size: 1.65rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )



def render_header_bar() -> None:
    header_container = st.container()
    with header_container:
        st.markdown('<div id="vf-header-anchor"></div>', unsafe_allow_html=True)
        brand_col, nav1, nav2, nav3, nav4 = st.columns([4.6, 1.35, 1.55, 0.95, 1.6], gap="medium")

        with brand_col:
            st.markdown(
                '<div class="vf-header-brand">Viabilidade-Fácil<span class="vf-header-dot">.</span></div>',
                unsafe_allow_html=True,
            )

        with nav1:
            st.markdown('<div class="vf-header-nav vf-header-nav--muted">', unsafe_allow_html=True)
            st.button("Como funciona", key="vf_nav_how", type="tertiary", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with nav2:
            st.markdown('<div class="vf-header-nav">', unsafe_allow_html=True)
            if st.button("Área do cliente", key="vf_nav_client", type="tertiary", use_container_width=True):
                st.session_state["show_client_area"] = True
                if not st.session_state.get("auth_logged_in"):
                    st.session_state["post_login_action"] = "open_client_area"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with nav3:
            st.markdown('<div class="vf-header-nav vf-header-nav--muted">', unsafe_allow_html=True)
            st.button("Planos", key="vf_nav_plans", type="tertiary", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with nav4:
            st.markdown('<div class="vf-header-nav vf-header-nav--muted">', unsafe_allow_html=True)
            st.button("Dúvida e suporte", key="vf_nav_support", type="tertiary", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
