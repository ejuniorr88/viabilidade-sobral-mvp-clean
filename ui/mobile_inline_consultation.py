from __future__ import annotations

"""Suporte mobile para posicionar o formulário da consulta abaixo do mapa."""

import streamlit as st


ANCHOR_CLASS = "vf-mobile-inline-consultation-anchor"
ANCHOR_ID = "vf-mobile-inline-consultation"


def inject_mobile_inline_consultation_styles() -> None:
    """Injeta somente o estilo do marcador invisível do formulário mobile."""

    st.markdown(
        f"""
        <style>
        .{ANCHOR_CLASS} {{
            display: none !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_mobile_inline_consultation_header() -> None:
    """Renderiza apenas um marcador invisível antes dos campos mobile."""

    inject_mobile_inline_consultation_styles()
    st.markdown(
        f'<div id="{ANCHOR_ID}" class="{ANCHOR_CLASS}" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )
