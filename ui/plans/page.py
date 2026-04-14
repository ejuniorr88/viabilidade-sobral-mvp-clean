from __future__ import annotations

import streamlit as st

from ui.payments_panel import render_payments_panel


def render_plans_page() -> None:
    st.markdown("## Adquirir planos")
    st.caption("Escolha um plano, gere o Pix e acompanhe seu pagamento. Os relatórios para download continuam exclusivos da Área do Cliente.")
    render_payments_panel()
