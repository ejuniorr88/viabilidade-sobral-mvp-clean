from __future__ import annotations

import streamlit as st

CHECKOUT_STATE_KEYS = [
    "landing_checkout_mode",
    "landing_selected_plan_slug",
    "payments_focus_mode",
    "current_payment_id",
    "current_payment_snapshot",
    "pix_created_success",
    "show_all_plans_override",
]

def clear_all_checkout_states() -> None:
    """
    Limpa de forma explícita o contexto de checkout.
    Deve ser chamada apenas em ações diretas do usuário.
    """
    for key in CHECKOUT_STATE_KEYS:
        st.session_state.pop(key, None)
