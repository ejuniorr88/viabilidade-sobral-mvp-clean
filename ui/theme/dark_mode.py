from __future__ import annotations

import streamlit as st


MAIN_TEXT = "#1f2a44"
MUTED_TEXT = "#4b5563"
WHITE = "#ffffff"
HEADER_BLUE = "#071847"
HEADER_ORANGE = "#d68910"


def inject_dark_mode_text_safety() -> None:
    """Centralized protection for the app's light layout in dark mode.

    The system intentionally uses a light main surface. When the browser or
    Streamlit is in dark mode, Streamlit can apply light text tokens over the
    app's forced white cards/backgrounds, making content almost invisible until
    hover. This fix is intentionally isolated from ui/app_shell.py.

    Scope rules:
    - fix only the main app surface / block container;
    - preserve the already-approved dark sidebar and top navigation;
    - avoid changing business logic, auth, credits, payments or reports.
    """
    st.markdown(
        f"""
        <style id="vf-dark-mode-text-safety">
        html,
        body,
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] .main,
        [data-testid="stAppViewContainer"] .block-container {{
            color-scheme: light !important;
        }}

        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] .main,
        [data-testid="stAppViewContainer"] .block-container {{
            background: {WHITE} !important;
            color: {MAIN_TEXT} !important;
        }}

        [data-testid="stAppViewContainer"] .block-container {{
            --text-color: {MAIN_TEXT} !important;
            --body-text-color: {MAIN_TEXT} !important;
            --background-color: {WHITE} !important;
            --secondary-background-color: #f8fafc !important;
        }}

        [data-testid="stAppViewContainer"] .block-container :where(
            h1, h2, h3, h4, h5, h6,
            p, li, label, small, strong, em, span,
            div[data-testid="stMarkdownContainer"],
            div[data-testid="stMarkdownContainer"] *,
            div[data-testid="stCaptionContainer"],
            div[data-testid="stCaptionContainer"] *,
            div[data-testid="stMetric"],
            div[data-testid="stMetric"] *,
            div[data-testid="stAlert"],
            div[data-testid="stAlert"] *,
            .vf-report-container,
            .vf-report-container *,
            .vf-section-card,
            .vf-section-card *,
            .vf-summary-card,
            .vf-summary-card *
        ) {{
            color: {MAIN_TEXT} !important;
        }}

        [data-testid="stAppViewContainer"] .block-container :where(
            div[data-testid="stCaptionContainer"],
            div[data-testid="stCaptionContainer"] *,
            .vf-muted,
            .vf-muted *,
            .vf-summary-label
        ) {{
            color: {MUTED_TEXT} !important;
        }}

        [data-testid="stAppViewContainer"] .block-container :where(
            a,
            a *
        ) {{
            color: #0f62fe !important;
        }}

        /* Preserve the approved dark header and mobile navigation identity. */
        [data-testid="stHorizontalBlock"]:has(.vf-brand),
        [data-testid="stHorizontalBlock"]:has(.vf-brand) *,
        .vf-brand,
        .vf-brand *,
        .vf-nav-link-button,
        .vf-nav-link-button *,
        .vf-mobile-shell,
        .vf-mobile-shell * {{
            color: {WHITE} !important;
        }}

        .vf-brand-dot,
        .vf-mobile-brand-dot {{
            color: {HEADER_ORANGE} !important;
        }}

        /* Preserve report/header badges that are intentionally light on dark/colored surfaces. */
        [data-testid="stAppViewContainer"] .block-container :where(
            .vf-hero,
            .vf-hero *,
            .vf-section-badge,
            .vf-section-badge *
        ) {{
            color: {WHITE} !important;
        }}

        /* Keep primary/dark buttons readable and avoid changing their layout. */
        [data-testid="stAppViewContainer"] .block-container .stButton button[kind="primary"],
        [data-testid="stAppViewContainer"] .block-container .stButton button[kind="primary"] * {{
            color: {WHITE} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
