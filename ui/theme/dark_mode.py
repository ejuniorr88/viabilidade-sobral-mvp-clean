from __future__ import annotations

import streamlit as st

MAIN_TEXT = "#061a3a"
MUTED_TEXT = "#42526b"
WHITE = "#ffffff"
DARK_BUTTON = "#111827"
DARK_BUTTON_HOVER = "#1f2937"
LINK = "#0b5fff"


def inject_dark_mode_readability_fix() -> None:
    """Isolated readability fix for Streamlit dark mode.

    The app shell keeps the main content on a white surface. In dark mode,
    Streamlit can render many labels and markdown fragments as light text,
    making them almost invisible. This module only fixes contrast inside the
    main content block. It does not touch sidebar styling, global scrollbars,
    auth, credits, payments, reports, routing or urbanistic rules.
    """
    st.markdown(
        f"""
        <style id="vf-dark-mode-readability-fix-v9">
        [data-testid="stAppViewContainer"] .block-container :where(
            h1, h2, h3, h4, h5, h6,
            p, li, label, small, strong, em,
            div[data-testid="stMarkdownContainer"],
            div[data-testid="stMarkdownContainer"] *,
            div[data-testid="stCaptionContainer"],
            div[data-testid="stCaptionContainer"] *,
            div[data-testid="stMetric"], div[data-testid="stMetric"] *,
            div[data-testid="stAlert"], div[data-testid="stAlert"] *,
            .vf-card, .vf-card *,
            .vf-client-area, .vf-client-area *,
            .vf-wallet, .vf-wallet *,
            .vf-report-container, .vf-report-container *,
            .vf-section-card, .vf-section-card *,
            .vf-summary-card, .vf-summary-card *,
            .vf-report-snapshot, .vf-report-snapshot *,
            .vf-report-block, .vf-report-block *,
            .vf-report-item, .vf-report-item *,
            .vf-report-list, .vf-report-list *,
            .vf-table, .vf-table *,
            .legal-doc-wrap, .legal-doc-wrap *
        ) {{
            color: {MAIN_TEXT} !important;
            -webkit-text-fill-color: {MAIN_TEXT} !important;
            opacity: 1 !important;
            filter: none !important;
        }}

        [data-testid="stAppViewContainer"] .block-container :where(
            div[data-testid="stCaptionContainer"],
            div[data-testid="stCaptionContainer"] *,
            .vf-muted, .vf-muted *,
            .vf-summary-label, .vf-help, .vf-help *
        ) {{
            color: {MUTED_TEXT} !important;
            -webkit-text-fill-color: {MUTED_TEXT} !important;
            opacity: 1 !important;
            filter: none !important;
        }}

        [data-testid="stAppViewContainer"] .block-container :where(
            input, textarea, select,
            [data-baseweb="input"], [data-baseweb="input"] *,
            [data-baseweb="select"], [data-baseweb="select"] *,
            [data-baseweb="textarea"], [data-baseweb="textarea"] *,
            [role="combobox"], [role="combobox"] *
        ) {{
            color: {MAIN_TEXT} !important;
            -webkit-text-fill-color: {MAIN_TEXT} !important;
            opacity: 1 !important;
            filter: none !important;
        }}

        [data-testid="stAppViewContainer"] .block-container input::placeholder,
        [data-testid="stAppViewContainer"] .block-container textarea::placeholder {{
            color: {MUTED_TEXT} !important;
            -webkit-text-fill-color: {MUTED_TEXT} !important;
            opacity: 1 !important;
        }}

        [data-testid="stAppViewContainer"] .block-container div.stButton > button:not([kind="tertiary"]),
        [data-testid="stAppViewContainer"] .block-container div[data-testid="stDownloadButton"] > button {{
            background-color: {DARK_BUTTON} !important;
            border-color: {DARK_BUTTON} !important;
            color: {WHITE} !important;
            -webkit-text-fill-color: {WHITE} !important;
            opacity: 1 !important;
            filter: none !important;
        }}

        [data-testid="stAppViewContainer"] .block-container div.stButton > button:not([kind="tertiary"]) *,
        [data-testid="stAppViewContainer"] .block-container div[data-testid="stDownloadButton"] > button * {{
            color: {WHITE} !important;
            -webkit-text-fill-color: {WHITE} !important;
            opacity: 1 !important;
            filter: none !important;
        }}

        [data-testid="stAppViewContainer"] .block-container div.stButton > button:not([kind="tertiary"]):hover,
        [data-testid="stAppViewContainer"] .block-container div[data-testid="stDownloadButton"] > button:hover {{
            background-color: {DARK_BUTTON_HOVER} !important;
            border-color: {DARK_BUTTON_HOVER} !important;
            color: {WHITE} !important;
            -webkit-text-fill-color: {WHITE} !important;
        }}

        [data-testid="stAppViewContainer"] .block-container div.stButton > button:disabled,
        [data-testid="stAppViewContainer"] .block-container div.stButton > button[disabled],
        [data-testid="stAppViewContainer"] .block-container div.stButton > button[aria-disabled="true"],
        [data-testid="stAppViewContainer"] .block-container div[data-testid="stDownloadButton"] > button:disabled,
        [data-testid="stAppViewContainer"] .block-container div[data-testid="stDownloadButton"] > button[disabled],
        [data-testid="stAppViewContainer"] .block-container div[data-testid="stDownloadButton"] > button[aria-disabled="true"] {{
            background-color: {DARK_BUTTON} !important;
            border-color: {DARK_BUTTON} !important;
            color: {WHITE} !important;
            -webkit-text-fill-color: {WHITE} !important;
            opacity: 1 !important;
            filter: none !important;
            cursor: not-allowed !important;
        }}

        [data-testid="stAppViewContainer"] .block-container div.stButton > button:disabled *,
        [data-testid="stAppViewContainer"] .block-container div.stButton > button[disabled] *,
        [data-testid="stAppViewContainer"] .block-container div.stButton > button[aria-disabled="true"] *,
        [data-testid="stAppViewContainer"] .block-container div[data-testid="stDownloadButton"] > button:disabled *,
        [data-testid="stAppViewContainer"] .block-container div[data-testid="stDownloadButton"] > button[disabled] *,
        [data-testid="stAppViewContainer"] .block-container div[data-testid="stDownloadButton"] > button[aria-disabled="true"] * {{
            color: {WHITE} !important;
            -webkit-text-fill-color: {WHITE} !important;
            opacity: 1 !important;
            filter: none !important;
        }}

        [data-testid="stAppViewContainer"] .block-container a:not(.vf-nav-link-button):not(.vf-brand):not(.vf-mobile-brand),
        [data-testid="stAppViewContainer"] .block-container a:not(.vf-nav-link-button):not(.vf-brand):not(.vf-mobile-brand) * {{
            color: {LINK} !important;
            -webkit-text-fill-color: {LINK} !important;
        }}

        [data-testid="stHorizontalBlock"]:has(.vf-brand),
        [data-testid="stHorizontalBlock"]:has(.vf-brand) *,
        .vf-brand, .vf-brand *,
        .vf-nav-link-button, .vf-nav-link-button *,
        .vf-mobile-shell, .vf-mobile-shell * {{
            color: {WHITE} !important;
            -webkit-text-fill-color: {WHITE} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
