from __future__ import annotations

"""Apresentação mobile do formulário da consulta abaixo do mapa."""

import streamlit as st


def inject_mobile_inline_consultation_styles() -> None:
    """Injeta estilos específicos para o bloco de formulário no mobile."""

    st.markdown(
        """
        <style>
        .vf-mobile-inline-form-anchor {
            display: none !important;
        }

        @media (max-width: 768px) {
            .vf-mobile-inline-form-anchor {
                display: block !important;
                margin: 1rem 0 0.75rem 0 !important;
                padding: 0.95rem 1rem !important;
                border: 1px solid #e6eaf2 !important;
                border-radius: 18px !important;
                background: #ffffff !important;
                box-shadow: 0 10px 26px rgba(7, 24, 71, 0.08) !important;
            }

            .vf-mobile-inline-form-kicker {
                display: inline-flex !important;
                align-items: center !important;
                gap: 0.45rem !important;
                margin-bottom: 0.35rem !important;
                padding: 0.35rem 0.65rem !important;
                border-radius: 999px !important;
                background: rgba(214, 137, 16, 0.12) !important;
                color: #8a4b00 !important;
                font-size: 0.82rem !important;
                font-weight: 850 !important;
            }

            .vf-mobile-inline-form-title {
                margin: 0 !important;
                color: #071847 !important;
                font-size: 1.22rem !important;
                font-weight: 900 !important;
                line-height: 1.18 !important;
            }

            .vf-mobile-inline-form-text {
                margin: 0.45rem 0 0 !important;
                color: #3a4050 !important;
                font-size: 0.96rem !important;
                line-height: 1.35 !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_mobile_inline_consultation_header() -> None:
    """Renderiza chamada curta antes dos campos mobile da consulta."""

    inject_mobile_inline_consultation_styles()
    st.markdown(
        """
        <div id="vf-mobile-inline-consultation" class="vf-mobile-inline-form-anchor">
            <div class="vf-mobile-inline-form-kicker">📌 Dados da consulta</div>
            <h2 class="vf-mobile-inline-form-title">Preencha as informações do terreno</h2>
            <p class="vf-mobile-inline-form-text">
                No celular, os campos aparecem aqui embaixo do mapa. Depois de preencher,
                toque em gerar consulta aos índices urbanísticos.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
