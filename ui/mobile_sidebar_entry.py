from __future__ import annotations

import streamlit as st


def render_mobile_sidebar_entry() -> None:
    """Exibe uma chamada mobile clara para abrir o painel de dados da consulta.

    A sidebar continua sendo a fonte única dos campos para preservar as keys dos
    widgets já consolidados. No mobile, este módulo faz duas coisas:
    1. mostra uma orientação visível abaixo do cabeçalho;
    2. transforma o controle nativo da sidebar em um botão/pílula mais evidente.

    Escopo protegido:
    - não altera auth, pagamentos, carteira, cálculo, mapa ou relatório;
    - não duplica os widgets da sidebar;
    - não altera as keys já consolidadas de uso/lote.
    """

    st.markdown(
        """
<style>
.vf-mobile-sidebar-entry {
  display: none;
}

@media (max-width: 768px) {
  .vf-mobile-sidebar-entry {
    display: block;
    margin: 12px 0 18px 0;
    padding: 15px 15px 14px 15px;
    border: 1px solid rgba(15, 23, 42, 0.10);
    border-radius: 18px;
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    box-shadow: 0 12px 34px rgba(15, 23, 42, 0.08);
  }

  .vf-mobile-sidebar-entry__eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    margin-bottom: 8px;
    padding: 5px 10px;
    border-radius: 999px;
    background: rgba(245, 158, 11, 0.13);
    color: #92400e;
    font-size: 0.78rem;
    font-weight: 850;
    letter-spacing: .01em;
  }

  .vf-mobile-sidebar-entry__title {
    margin: 0 0 6px 0;
    color: #111827;
    font-size: 1.05rem;
    font-weight: 900;
    line-height: 1.22;
  }

  .vf-mobile-sidebar-entry__text {
    margin: 0 0 12px 0;
    color: #4b5563;
    font-size: 0.93rem;
    line-height: 1.42;
  }

  .vf-mobile-sidebar-entry__hint {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 11px 12px;
    border-radius: 14px;
    background: #0b1f55;
    color: #ffffff;
    font-weight: 850;
    line-height: 1.25;
  }

  .vf-mobile-sidebar-entry__icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.14);
    border: 1px solid rgba(255, 255, 255, 0.20);
    color: #f59e0b;
    font-size: 1.05rem;
    flex: 0 0 auto;
  }

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

<div class="vf-mobile-sidebar-entry" aria-label="Orientação para abrir os dados da consulta no celular">
  <div class="vf-mobile-sidebar-entry__eyebrow">📌 Comece por aqui</div>
  <div class="vf-mobile-sidebar-entry__title">Preencha os dados do terreno</div>
  <p class="vf-mobile-sidebar-entry__text">
    No celular, os campos da consulta ficam no painel lateral para economizar espaço.
  </p>
  <div class="vf-mobile-sidebar-entry__hint">
    <span class="vf-mobile-sidebar-entry__icon">»</span>
    <span>Toque em <strong>Abrir dados</strong>, no canto esquerdo, para preencher a consulta.</span>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
