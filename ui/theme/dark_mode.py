from __future__ import annotations

import streamlit as st

MAIN_TEXT = "#0f1f3d"
MUTED_TEXT = "#475569"
WHITE = "#ffffff"
SURFACE = "#f8fafc"
BORDER = "#d6dce8"
HEADER_ORANGE = "#d68910"
LINK = "#0f62fe"
DARK_BUTTON = "#111827"
DARK_BUTTON_HOVER = "#1f2937"
SCROLL_THUMB = "#8a94a6"
SCROLL_THUMB_HOVER = "#5f6878"
SCROLL_TRACK = "#eef2f7"
SIDEBAR_SCROLL_THUMB = "#a2a8b5"
SIDEBAR_SCROLL_THUMB_HOVER = "#c0c5cf"
SIDEBAR_SCROLL_TRACK = "#252836"


def inject_dark_mode_text_safety() -> None:
    """Keep the light visual identity readable when Streamlit/browser dark mode is active.

    This module intentionally stays outside ui/app_shell.py. It only injects CSS
    for contrast, Streamlit form controls, action buttons and scrollbars. It does
    not touch auth, credits, payments, reports persistence or urbanistic rules.
    """
    st.markdown(
        f"""
        <style id="vf-dark-mode-text-safety-v6">
        :root {{
            color-scheme: light !important;
            --vf-main-text: {MAIN_TEXT};
            --vf-muted-text: {MUTED_TEXT};
            --vf-surface: {SURFACE};
            --vf-border: {BORDER};
        }}

        html, body, .stApp, .stMain, .stMainBlockContainer, section.main,
        section[data-testid="stMain"], [data-testid="stApp"],
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] .main,
        [data-testid="stAppViewContainer"] .block-container {{
            color-scheme: light !important;
        }}

        html, body, .stApp, .stMain, [data-testid="stAppViewContainer"] {{
            background: {WHITE} !important;
            color: {MAIN_TEXT} !important;
        }}

        [data-testid="stAppViewContainer"] .block-container,
        .stMainBlockContainer,
        section.main .block-container,
        section[data-testid="stMain"] .block-container {{
            background: {WHITE} !important;
            color: {MAIN_TEXT} !important;
            --text-color: {MAIN_TEXT} !important;
            --body-text-color: {MAIN_TEXT} !important;
            --background-color: {WHITE} !important;
            --secondary-background-color: {SURFACE} !important;
        }}

        html {{
            overflow-y: scroll !important;
            scrollbar-gutter: stable both-edges !important;
        }}

        html, body, .stApp, .stMain, section.main, section[data-testid="stMain"],
        [data-testid="stAppViewContainer"], [data-testid="stMain"],
        [data-testid="stVerticalBlock"], [data-testid="stSidebar"],
        [data-testid="stSidebarContent"], * {{
            scrollbar-width: auto !important;
            scrollbar-color: {SCROLL_THUMB} {SCROLL_TRACK} !important;
        }}

        *::-webkit-scrollbar {{
            width: 16px !important;
            height: 16px !important;
            display: block !important;
        }}

        *::-webkit-scrollbar-track {{
            background: {SCROLL_TRACK} !important;
        }}

        *::-webkit-scrollbar-thumb {{
            background-color: {SCROLL_THUMB} !important;
            border: 3px solid {SCROLL_TRACK} !important;
            border-radius: 999px !important;
            min-height: 44px !important;
        }}

        *::-webkit-scrollbar-thumb:hover {{
            background-color: {SCROLL_THUMB_HOVER} !important;
        }}

        [data-testid="stSidebar"], [data-testid="stSidebarContent"],
        section[data-testid="stSidebar"] {{
            scrollbar-color: {SIDEBAR_SCROLL_THUMB} {SIDEBAR_SCROLL_TRACK} !important;
        }}

        [data-testid="stSidebar"]::-webkit-scrollbar-track,
        [data-testid="stSidebarContent"]::-webkit-scrollbar-track,
        section[data-testid="stSidebar"]::-webkit-scrollbar-track {{
            background: {SIDEBAR_SCROLL_TRACK} !important;
        }}

        [data-testid="stSidebar"]::-webkit-scrollbar-thumb,
        [data-testid="stSidebarContent"]::-webkit-scrollbar-thumb,
        section[data-testid="stSidebar"]::-webkit-scrollbar-thumb {{
            background-color: {SIDEBAR_SCROLL_THUMB} !important;
            border: 3px solid {SIDEBAR_SCROLL_TRACK} !important;
            border-radius: 999px !important;
        }}

        [data-testid="stSidebar"]::-webkit-scrollbar-thumb:hover,
        [data-testid="stSidebarContent"]::-webkit-scrollbar-thumb:hover,
        section[data-testid="stSidebar"]::-webkit-scrollbar-thumb:hover {{
            background-color: {SIDEBAR_SCROLL_THUMB_HOVER} !important;
        }}

        [data-testid="stAppViewContainer"] .block-container :where(
            h1, h2, h3, h4, h5, h6, p, li, label, small, strong, em,
            span:not(.vf-brand-dot):not(.vf-mobile-brand-dot),
            div[data-testid="stMarkdownContainer"],
            div[data-testid="stMarkdownContainer"] *,
            div[data-testid="stCaptionContainer"],
            div[data-testid="stCaptionContainer"] *,
            div[data-testid="stMetric"], div[data-testid="stMetric"] *,
            div[data-testid="stAlert"], div[data-testid="stAlert"] *,
            .vf-card, .vf-card *, .vf-client-area, .vf-client-area *,
            .vf-wallet, .vf-wallet *, .vf-report-container, .vf-report-container *,
            .vf-section-card, .vf-section-card *, .vf-summary-card, .vf-summary-card *,
            .vf-report-snapshot, .vf-report-snapshot *, .vf-report-block, .vf-report-block *,
            .vf-report-item, .vf-report-item *, .vf-report-list, .vf-report-list *,
            .vf-table, .vf-table *, .legal-doc-wrap, .legal-doc-wrap *
        ) {{
            color: {MAIN_TEXT} !important;
            -webkit-text-fill-color: {MAIN_TEXT} !important;
            opacity: 1 !important;
        }}

        [data-testid="stAppViewContainer"] .block-container :where(
            div[data-testid="stCaptionContainer"], div[data-testid="stCaptionContainer"] *,
            .vf-muted, .vf-muted *, .vf-summary-label, .vf-help, .vf-help *
        ) {{
            color: {MUTED_TEXT} !important;
            -webkit-text-fill-color: {MUTED_TEXT} !important;
            opacity: 1 !important;
        }}

        [data-testid="stAppViewContainer"] .block-container :where(
            input, textarea, select, [data-baseweb="input"], [data-baseweb="input"] *,
            [data-baseweb="select"], [data-baseweb="select"] *,
            [data-baseweb="textarea"], [data-baseweb="textarea"] *,
            [role="combobox"], [role="combobox"] *
        ) {{
            background-color: {WHITE} !important;
            color: {MAIN_TEXT} !important;
            -webkit-text-fill-color: {MAIN_TEXT} !important;
            opacity: 1 !important;
        }}

        [data-testid="stAppViewContainer"] .block-container input::placeholder,
        [data-testid="stAppViewContainer"] .block-container textarea::placeholder {{
            color: {MUTED_TEXT} !important;
            -webkit-text-fill-color: {MUTED_TEXT} !important;
            opacity: 1 !important;
        }}

        [data-testid="stAppViewContainer"] .block-container div.stButton > button:not([kind="tertiary"]),
        [data-testid="stAppViewContainer"] .block-container div.stButton > button[data-testid="baseButton-primary"],
        [data-testid="stAppViewContainer"] .block-container div.stButton > button[data-testid="baseButton-secondary"] {{
            background-color: {DARK_BUTTON} !important;
            border-color: {DARK_BUTTON} !important;
            color: {WHITE} !important;
            -webkit-text-fill-color: {WHITE} !important;
            opacity: 1 !important;
        }}

        [data-testid="stAppViewContainer"] .block-container div.stButton > button:not([kind="tertiary"]) *,
        [data-testid="stAppViewContainer"] .block-container div.stButton > button[data-testid="baseButton-primary"] *,
        [data-testid="stAppViewContainer"] .block-container div.stButton > button[data-testid="baseButton-secondary"] * {{
            color: {WHITE} !important;
            -webkit-text-fill-color: {WHITE} !important;
            opacity: 1 !important;
        }}

        [data-testid="stAppViewContainer"] .block-container div.stButton > button:not([kind="tertiary"]):hover {{
            background-color: {DARK_BUTTON_HOVER} !important;
            border-color: {DARK_BUTTON_HOVER} !important;
            color: {WHITE} !important;
            -webkit-text-fill-color: {WHITE} !important;
        }}

        [data-testid="stAppViewContainer"] .block-container div.stButton > button:disabled,
        [data-testid="stAppViewContainer"] .block-container div.stButton > button[disabled],
        [data-testid="stAppViewContainer"] .block-container div.stButton > button[aria-disabled="true"] {{
            filter: none !important;
            opacity: 1 !important;
            background-color: {DARK_BUTTON} !important;
            border-color: {DARK_BUTTON} !important;
            color: {WHITE} !important;
            -webkit-text-fill-color: {WHITE} !important;
        }}

        [data-testid="stAppViewContainer"] .block-container div.stButton > button:disabled *,
        [data-testid="stAppViewContainer"] .block-container div.stButton > button[disabled] *,
        [data-testid="stAppViewContainer"] .block-container div.stButton > button[aria-disabled="true"] * {{
            color: {WHITE} !important;
            -webkit-text-fill-color: {WHITE} !important;
            opacity: 1 !important;
        }}

        [data-testid="stAppViewContainer"] .block-container :where(a, a *) {{
            color: {LINK} !important;
            -webkit-text-fill-color: {LINK} !important;
        }}

        [data-testid="stAppViewContainer"] .block-container :where(
            hr, .vf-card, .vf-report-container, .vf-section-card, .vf-summary-card,
            .vf-report-snapshot, .vf-report-block, .vf-report-item, .legal-doc-wrap
        ) {{
            border-color: {BORDER} !important;
        }}

        [data-testid="stHorizontalBlock"]:has(.vf-brand),
        [data-testid="stHorizontalBlock"]:has(.vf-brand) *,
        .vf-brand, .vf-brand *, .vf-nav-link-button, .vf-nav-link-button *,
        .vf-mobile-shell, .vf-mobile-shell * {{
            color: {WHITE} !important;
            -webkit-text-fill-color: {WHITE} !important;
        }}

        .vf-brand-dot, .vf-mobile-brand-dot {{
            color: {HEADER_ORANGE} !important;
            -webkit-text-fill-color: {HEADER_ORANGE} !important;
        }}

        [data-testid="stAppViewContainer"] .block-container :where(
            .vf-hero, .vf-hero *, .vf-section-badge, .vf-section-badge *,
            .vf-status-badge, .vf-status-badge *,
            .vf-info-box.success, .vf-info-box.success *,
            .vf-info-box.warning, .vf-info-box.warning *,
            .vf-info-box.danger, .vf-info-box.danger *
        ) {{
            color: {WHITE} !important;
            -webkit-text-fill-color: {WHITE} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
