from __future__ import annotations

"""
Mobile header implementation for Viabilidade Fácil's Streamlit app.

This module isolates the code required to render a responsive mobile
navigation bar. On small screens the traditional desktop header is
hidden and a compact mobile header appears in its place. The mobile
header includes a toggle button (hamburger / close icon), links to
external landing pages and a button to open the "Área do cliente" using
the same session logic as the desktop interface.
"""

from typing import Callable
import streamlit as st


def inject_mobile_header_styles() -> None:
    """Inject scoped CSS rules for the mobile header.

    The CSS generated here hides the desktop header when the viewport
    width is below 769px and hides the mobile header when the viewport
    width is larger. It also defines the look and feel of the mobile
    header, including the top bar, toggle button and navigation panel.
    """
    st.markdown(
        '''
        <style>
        /* Hide the custom mobile header on larger screens */
        @media (min-width: 769px) {
            .vf-mobile-shell {
                display: none !important;
            }
        }
        /* Hide the desktop header on small screens by targeting the branded horizontal block */
        @media (max-width: 768px) {
            [data-testid="stHorizontalBlock"]:has(.vf-brand) {
                display: none !important;
            }
        }

        /* Container for the entire mobile header */
        .vf-mobile-shell {
            width: 100%;
            position: relative;
            z-index: 9999;
        }

        /* Top bar styling */
        .vf-mobile-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #071847;
            border-bottom: 3px solid #d68910;
            padding: 0.5rem 1rem;
            min-height: 56px;
        }

        .vf-mobile-brand {
            font-size: 24px;
            font-weight: 800;
            color: #ffffff;
            text-decoration: none;
            letter-spacing: -0.02em;
            line-height: 1;
            display: flex;
            align-items: center;
            white-space: nowrap;
        }

        .vf-mobile-brand-dot {
            color: #d68910;
            margin-left: 2px;
        }

        /* Generic button resets for any button inside the mobile shell */
        .vf-mobile-shell .stButton>button {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #ffffff !important;
            padding: 0.25rem 0.5rem !important;
            line-height: 1 !important;
            font-weight: 600 !important;
            border-radius: 0 !important;
            cursor: pointer !important;
        }

        .vf-mobile-shell .stButton>button:hover {
            opacity: 0.8 !important;
            background: transparent !important;
        }

        /* Toggle button specific sizing */
        .vf-mobile-bar .stButton>button {
            font-size: 28px !important;
        }

        /* Navigation panel styling */
        .vf-mobile-panel {
            width: 100%;
            background-color: #071847;
            padding: 0.5rem 0;
        }

        /* Links and buttons inside the panel share the same look */
        .vf-mobile-panel a,
        .vf-mobile-panel .stButton>button {
            display: block;
            width: 100%;
            text-align: left;
            padding: 0.75rem 1rem;
            font-size: 16px;
            font-weight: 600;
            color: #ffffff;
            text-decoration: none;
            border-top: 1px solid rgba(255,255,255,0.1);
        }

        /* Remove top border on the first item to avoid a double line */
        .vf-mobile-panel a:first-child,
        .vf-mobile-panel .stButton:first-child>button {
            border-top: none;
        }

        .vf-mobile-panel a:hover,
        .vf-mobile-panel .stButton>button:hover {
            color: #d68910;
        }
        </style>
        ''',
        unsafe_allow_html=True,
    )


def render_mobile_top_nav(
    *,
    brand: str,
    home_url: str,
    how_url: str,
    plans_url: str,
    support_url: str,
    on_open_client_area: Callable[[], None],
) -> None:
    """Render a responsive mobile navigation bar.

    Parameters
    ----------
    brand:
        Text label for the brand (e.g. "Viabilidade-Fácil").
    home_url:
        URL to the home route of the app.
    how_url:
        Landing page URL for the "Como funciona" section.
    plans_url:
        Landing page URL for the "Planos" page.
    support_url:
        Landing page URL for the "Dúvidas/Suporte" page.
    on_open_client_area:
        Callback executed when the user clicks "Área do cliente" in the
        mobile menu. This callback should replicate the behaviour of the
        desktop header by updating session state and rerunning the app.
    """
    # Initialize the toggle state on first render
    if 'vf_mobile_nav_open' not in st.session_state:
        st.session_state.vf_mobile_nav_open = False

    # Begin the mobile header container
    st.markdown('<div class="vf-mobile-shell">', unsafe_allow_html=True)

    # Render the top bar with brand and toggle button
    st.markdown('<div class="vf-mobile-bar">', unsafe_allow_html=True)

    # Brand link to home
    st.markdown(
        f'<a class="vf-mobile-brand" href="{home_url}" target="_self" aria-label="Ir para a página inicial do sistema">{brand}<span class="vf-mobile-brand-dot">.</span></a>',
        unsafe_allow_html=True,
    )

    # Toggle button: ☰ when closed, ✕ when open
    icon = '✕' if st.session_state.vf_mobile_nav_open else '☰'
    if st.button(icon, key='vf_mobile_nav_toggle'):
        st.session_state.vf_mobile_nav_open = not st.session_state.vf_mobile_nav_open

    st.markdown('</div>', unsafe_allow_html=True)  # close vf-mobile-bar

    # Render the navigation panel if the menu is open
    if st.session_state.vf_mobile_nav_open:
        st.markdown('<div class="vf-mobile-panel">', unsafe_allow_html=True)

        # "Como funciona" link
        st.markdown(
            f'<a href="{how_url}" target="_self" aria-label="Abrir página Como funciona na mesma aba">Como funciona</a>',
            unsafe_allow_html=True,
        )

        # "Área do cliente" uses a button so Python can handle session updates
        if st.button('Área do cliente', key='vf_mobile_nav_client_area', type='tertiary'):
            # Close the menu before invoking the callback to avoid leftover state
            st.session_state.vf_mobile_nav_open = False
            on_open_client_area()

        # "Planos" link
        st.markdown(
            f'<a href="{plans_url}" target="_self" aria-label="Abrir página de planos na mesma aba">Planos</a>',
            unsafe_allow_html=True,
        )

        # "Dúvidas/Suporte" link
        st.markdown(
            f'<a href="{support_url}" target="_self" aria-label="Abrir página de dúvidas e suporte na mesma aba">Dúvidas/Suporte</a>',
            unsafe_allow_html=True,
        )

        st.markdown('</div>', unsafe_allow_html=True)  # close vf-mobile-panel

    st.markdown('</div>', unsafe_allow_html=True)  # close vf-mobile-shell
