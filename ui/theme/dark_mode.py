from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components


def inject_dark_mode_text_fixes() -> None:
    """Corrige legibilidade apenas quando o Streamlit estiver no modo escuro.

    Regras desta frente:
    - não altera o ui/app_shell.py;
    - não mexe em scrollbar;
    - não mexe na sidebar;
    - não estiliza globalmente todos os botões;
    - não altera o botão principal de consulta no modo claro;
    - aplica correções de texto somente sob html[data-theme="dark"].
    """

    st.markdown(
        """
        <style id="vf-dark-mode-text-fixes">
        html[data-theme="dark"] [data-testid="stAppViewContainer"] {
            color: #f8fafc !important;
        }

        html[data-theme="dark"] .block-container,
        html[data-theme="dark"] .block-container p,
        html[data-theme="dark"] .block-container span,
        html[data-theme="dark"] .block-container label,
        html[data-theme="dark"] .block-container li,
        html[data-theme="dark"] .block-container div:not([data-testid="stDecoration"]),
        html[data-theme="dark"] .vf-report-container,
        html[data-theme="dark"] .vf-report-container *,
        html[data-theme="dark"] .vf-section-card,
        html[data-theme="dark"] .vf-section-card *,
        html[data-theme="dark"] .vf-summary-card,
        html[data-theme="dark"] .vf-summary-card * {
            color: #f8fafc !important;
        }

        html[data-theme="dark"] .block-container a,
        html[data-theme="dark"] .vf-report-container a {
            color: #93c5fd !important;
        }

        html[data-theme="dark"] input,
        html[data-theme="dark"] textarea,
        html[data-theme="dark"] [data-baseweb="select"] *,
        html[data-theme="dark"] [data-baseweb="input"] *,
        html[data-theme="dark"] [data-baseweb="textarea"] * {
            color: #f8fafc !important;
        }

        html[data-theme="dark"] div[data-testid="stDownloadButton"] button,
        html[data-theme="dark"] div[data-testid="stDownloadButton"] button * {
            color: #ffffff !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    components.html(
        """
        <script>
        (() => {
            const REPORT_TEXTS = [
                'gerar relatório do estudo de viabilidade',
                'gerar relatorio do estudo de viabilidade',
                'gerar relatório',
                'gerar relatorio'
            ];
            const DARK_BACKGROUND = 'linear-gradient(180deg, #1e3a5f 0%, #14294a 100%)';
            const DARK_BORDER = '1px solid #60a5fa';
            const DARK_COLOR = '#ffffff';
            const DARK_SHADOW = '0 2px 12px rgba(96, 165, 250, 0.22)';

            function isDarkMode(doc) {
                const htmlTheme = (doc.documentElement.getAttribute('data-theme') || '').toLowerCase();
                const appTheme = (doc.body.getAttribute('data-theme') || '').toLowerCase();
                return htmlTheme === 'dark' || appTheme === 'dark';
            }

            function normalizeButtonText(value) {
                return (value || '')
                    .toLowerCase()
                    .normalize('NFD')
                    .replace(/[\u0300-\u036f]/g, '')
                    .replace(/\s+/g, ' ')
                    .trim();
            }

            function findReportButton(doc) {
                return [...doc.querySelectorAll('div[data-testid="stButton"] button')]
                    .find((button) => {
                        const label = normalizeButtonText(button.innerText);
                        return REPORT_TEXTS.some((expected) => label.includes(normalizeButtonText(expected)));
                    });
            }

            function applyDarkReportButtonStyle(button) {
                button.dataset.vfDarkModeReportButton = '1';
                button.style.setProperty('background', DARK_BACKGROUND, 'important');
                button.style.setProperty('border', DARK_BORDER, 'important');
                button.style.setProperty('color', DARK_COLOR, 'important');
                button.style.setProperty('font-weight', '700', 'important');
                button.style.setProperty('box-shadow', DARK_SHADOW, 'important');

                [...button.querySelectorAll('*')].forEach((child) => {
                    child.style.setProperty('color', DARK_COLOR, 'important');
                });
            }

            function clearOnlyDarkReportButtonStyle(button) {
                if (button.dataset.vfDarkModeReportButton !== '1') return;
                delete button.dataset.vfDarkModeReportButton;
                ['background', 'border', 'color', 'font-weight', 'box-shadow'].forEach((prop) => {
                    button.style.removeProperty(prop);
                });
                [...button.querySelectorAll('*')].forEach((child) => {
                    child.style.removeProperty('color');
                });
            }

            function refresh() {
                const doc = window.parent.document;
                const button = findReportButton(doc);
                if (!button) return;

                if (isDarkMode(doc)) {
                    applyDarkReportButtonStyle(button);
                } else {
                    clearOnlyDarkReportButtonStyle(button);
                }
            }

            refresh();
            window.setTimeout(refresh, 120);
            window.setTimeout(refresh, 400);
            window.setTimeout(refresh, 900);
        })();
        </script>
        """,
        height=0,
    )
