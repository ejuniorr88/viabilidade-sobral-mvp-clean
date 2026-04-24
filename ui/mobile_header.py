from __future__ import annotations

"""
Mobile header implementation for Viabilidade Fácil's Streamlit app.

This module renders the mobile header as one single HTML/CSS block. Streamlit
native layout widgets are intentionally not used here because they do not
remain nested inside raw HTML wrappers created with markdown rendering. Keeping the mobile header as a single block prevents the
mobile shell from leaking into the desktop layout.
"""

from html import escape
from typing import Callable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import streamlit as st


def _with_query_param(url: str, key: str, value: str, *, remove_keys: set[str] | None = None) -> str:
    """Return *url* with one query parameter replaced safely."""
    remove_keys = remove_keys or set()
    parts = urlsplit(url or "")
    query = [
        (current_key, current_value)
        for current_key, current_value in parse_qsl(parts.query, keep_blank_values=True)
        if current_key not in remove_keys and current_key != key
    ]
    query.append((key, value))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def inject_mobile_header_styles() -> None:
    """Inject scoped CSS rules for the mobile header."""
    st.markdown(
        '''
        <style>
        /* The mobile shell is always hidden first. Only the mobile breakpoint can enable it. */
        .vf-mobile-shell {
            display: none !important;
        }

        @media (min-width: 769px) {
            .vf-mobile-shell,
            .vf-mobile-shell * {
                display: none !important;
                visibility: hidden !important;
                pointer-events: none !important;
                height: 0 !important;
                min-height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
                overflow: hidden !important;
            }
        }

        @media (max-width: 768px) {
            .vf-mobile-shell {
                display: block !important;
                width: 100% !important;
                position: relative !important;
                z-index: 9999 !important;
                margin: 0 0 1rem 0 !important;
            }

            /* Hide only the desktop branded Streamlit header row on mobile. */
            [data-testid="stHorizontalBlock"]:has(.vf-brand) {
                display: none !important;
                visibility: hidden !important;
                pointer-events: none !important;
                height: 0 !important;
                min-height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
                overflow: hidden !important;
            }
        }

        .vf-mobile-menu {
            width: 100%;
            background: #071847;
            border-bottom: 3px solid #d68910;
            box-shadow: 0 6px 18px rgba(7, 24, 71, 0.10);
        }

        .vf-mobile-check {
            position: absolute;
            opacity: 0;
            pointer-events: none;
            width: 1px;
            height: 1px;
        }

        .vf-mobile-bar {
            min-height: 58px;
            padding: 0 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
        }

        .vf-mobile-brand {
            color: #ffffff !important;
            text-decoration: none !important;
            font-size: 22px;
            font-weight: 800;
            letter-spacing: -0.02em;
            line-height: 1;
            white-space: nowrap;
        }

        .vf-mobile-brand:visited,
        .vf-mobile-brand:hover,
        .vf-mobile-brand:focus,
        .vf-mobile-brand:active {
            color: #ffffff !important;
            text-decoration: none !important;
        }

        .vf-mobile-brand-dot {
            color: #d68910;
            margin-left: 2px;
        }

        .vf-mobile-toggle {
            width: 42px;
            height: 42px;
            min-width: 42px;
            border: 1px solid rgba(255,255,255,0.28);
            border-radius: 10px;
            color: #ffffff;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 23px;
            font-weight: 700;
            line-height: 1;
            cursor: pointer;
            user-select: none;
            background: rgba(255,255,255,0.06);
            transition: background 0.18s ease, border-color 0.18s ease;
        }

        .vf-mobile-toggle:hover,
        .vf-mobile-toggle:focus {
            background: rgba(255,255,255,0.14);
            border-color: rgba(255,255,255,0.45);
            outline: none;
        }

        .vf-mobile-icon-close {
            display: none;
            font-size: 26px;
            transform: translateY(-1px);
        }

        .vf-mobile-check:checked ~ .vf-mobile-bar .vf-mobile-icon-open {
            display: none;
        }

        .vf-mobile-check:checked ~ .vf-mobile-bar .vf-mobile-icon-close {
            display: inline-block;
        }

        .vf-mobile-panel {
            display: none;
            flex-direction: column;
            width: 100%;
            padding: 8px 0 10px 0;
            background: #071847;
            border-top: 1px solid rgba(255,255,255,0.10);
        }

        .vf-mobile-check:checked ~ .vf-mobile-panel {
            display: flex;
        }

        .vf-mobile-panel a {
            display: block;
            width: 100%;
            box-sizing: border-box;
            padding: 13px 18px;
            color: #ffffff !important;
            text-decoration: none !important;
            font-size: 15px;
            font-weight: 650;
            line-height: 1.2;
            border-top: 1px solid rgba(255,255,255,0.08);
        }

        .vf-mobile-panel a:first-child {
            border-top: none;
        }

        .vf-mobile-panel a:hover,
        .vf-mobile-panel a:focus {
            color: #ffffff !important;
            background: rgba(255,255,255,0.12);
            text-decoration: none !important;
            outline: none;
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
    """Render the mobile navigation bar.

    The callback parameter is kept in the signature to preserve the existing
    ``ui.app_shell`` contract. The mobile header cannot call that callback
    directly without reintroducing native Streamlit buttons inside raw HTML. For this
    isolated mobile-only header, the "Área do cliente" item uses the app's
    existing ``client_area=1`` query-param handoff, which is consumed by
    ``consume_client_area_query_param(...)`` during runtime bootstrap.
    """

    # Preserve the public call contract without mixing Streamlit widgets inside
    # this HTML block. Mixing them caused the mobile header to leak into desktop.
    _ = on_open_client_area

    safe_brand = escape(brand or "Viabilidade-Fácil")
    safe_home_url = escape(home_url or "#", quote=True)
    safe_how_url = escape(how_url or "#", quote=True)
    safe_plans_url = escape(plans_url or "#", quote=True)
    safe_support_url = escape(support_url or "#", quote=True)
    safe_client_area_url = escape(
        _with_query_param(home_url or "#", "client_area", "1", remove_keys={"nav"}),
        quote=True,
    )

    st.markdown(
        f'''
        <div class="vf-mobile-shell" aria-label="Navegação mobile do sistema">
            <div class="vf-mobile-menu">
                <input id="vf-mobile-nav-check" class="vf-mobile-check" type="checkbox" aria-hidden="true" tabindex="-1" />
                <div class="vf-mobile-bar">
                    <a class="vf-mobile-brand" href="{safe_home_url}" target="_self" aria-label="Ir para a página inicial do sistema">
                        {safe_brand}<span class="vf-mobile-brand-dot">.</span>
                    </a>
                    <label class="vf-mobile-toggle" for="vf-mobile-nav-check" aria-label="Abrir ou fechar menu mobile" role="button" tabindex="0">
                        <span class="vf-mobile-icon-open" aria-hidden="true">☰</span>
                        <span class="vf-mobile-icon-close" aria-hidden="true">×</span>
                    </label>
                </div>
                <nav class="vf-mobile-panel" aria-label="Menu mobile">
                    <a href="{safe_how_url}" target="_self">Como funciona</a>
                    <a href="{safe_client_area_url}" target="_self">Área do cliente</a>
                    <a href="{safe_plans_url}" target="_self">Planos</a>
                    <a href="{safe_support_url}" target="_self">Dúvidas/Suporte</a>
                </nav>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )
