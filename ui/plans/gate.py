from __future__ import annotations

from typing import Optional

import streamlit as st

from ui.auth_panel import render_google_login_box
from ui.plans.page import render_plans_page


def _close_plans_page() -> None:
    st.session_state["show_plans_page"] = False


def render_plans_gate(*, user_logged_in: bool, user_id: Optional[str]) -> None:
    if st.button("← Voltar para o estudo", key="plans_page_back"):
        _close_plans_page()
        st.rerun()

    if user_logged_in and user_id:
        render_plans_page()
        return

    st.markdown("## Adquirir planos")
    st.info("Faça login com Google para comprar créditos, gerar Pix e acompanhar seus pagamentos.")
    render_google_login_box(
        title="Faça login para continuar",
        message="Entre com sua conta Google para adquirir planos e vincular os créditos à sua carteira.",
        context="plans_gate",
    )
