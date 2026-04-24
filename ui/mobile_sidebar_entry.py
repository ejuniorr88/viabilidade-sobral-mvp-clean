from __future__ import annotations

import streamlit as st


def render_mobile_sidebar_entry() -> None:
    """Reforça o controle nativo da sidebar no mobile sem exibir card extra.

    A sidebar continua sendo a fonte única dos campos para preservar as keys dos
    widgets já consolidados. No mobile, este módulo apenas deixa o controle nativo
    da sidebar mais evidente com o texto "Abrir dados".

    Escopo protegido:
    - não altera auth, pagamentos, carteira, cálculo, mapa ou relatório;
    - não duplica os widgets da sidebar;
    - não altera as keys já consolidadas de uso/lote;
    - não exibe card/mensagem de orientação abaixo do cabeçalho.
    """

    st.markdown(
        """
<style>
@media (max-width: 768px) {
  /* Reforça o controle nativo que abre a sidebar no mobile. */
  [data-testid="stSidebarCollapsedControl"] {
    position: fixed !important;
    top: 92px !important;
    left: 12px !important;
    z-index: 999999 !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 7px !important;
    min-height: 42px !important;
    padding: 5px 11px 5px 5px !important;
    border-radius: 999px !important;
    background: #ffffff !important;
    border: 1px solid rgba(15, 23, 42, 0.13) !important;
    box-shadow: 0 12px 28px rgba(15, 23, 42, 0.16) !important;
  }

  [data-testid="stSidebarCollapsedControl"]::after {
    content: "Abrir dados";
    color: #0b1f55;
    font-size: 0.82rem;
    font-weight: 900;
    white-space: nowrap;
    pointer-events: none;
  }

  [data-testid="stSidebarCollapsedControl"] button {
    min-width: 34px !important;
    min-height: 34px !important;
    width: 34px !important;
    height: 34px !important;
    border-radius: 999px !important;
    background: #0b1f55 !important;
    color: #ffffff !important;
    border: 1px solid rgba(15, 23, 42, 0.08) !important;
    box-shadow: none !important;
  }

  [data-testid="stSidebarCollapsedControl"] svg {
    color: #ffffff !important;
    stroke: #ffffff !important;
  }
}
</style>
        """,
        unsafe_allow_html=True,
    )
