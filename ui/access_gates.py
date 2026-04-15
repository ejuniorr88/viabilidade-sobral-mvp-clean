from __future__ import annotations

from typing import Any, MutableMapping, Optional

import streamlit as st

from ui.auth_panel import render_google_login_box
from ui.client_area import render_client_area_page


def _clear_client_area_checkout_state() -> None:
    st.session_state["show_client_area"] = False
    st.session_state["show_plans_page"] = False
    st.session_state["landing_checkout_mode"] = False
    st.session_state["landing_selected_plan_slug"] = None
    st.session_state["payments_focus_mode"] = False


def render_login_gate_block() -> None:
    render_google_login_box(
        title="Faça login para continuar",
        message="Para liberar a pesquisa de viabilidade, entre com sua conta Google.",
        context="login_gate",
    )


def render_client_area_gate(
    *,
    user_logged_in: bool,
    user_id: Optional[str],
    user_name: str,
    user_email: str,
    credit_balance: Optional[int],
) -> None:
    if user_logged_in and user_id:
        if st.button("← Voltar para o estudo", key="client_area_back"):
            _clear_client_area_checkout_state()
            st.rerun()
        render_client_area_page(
            user_id=user_id,
            user_name=user_name,
            user_email=user_email or "—",
            credit_balance=credit_balance,
        )
        return

    if st.button("← Voltar para o estudo", key="client_area_back_guest"):
        _clear_client_area_checkout_state()
        st.rerun()
    st.markdown("## Área do cliente")
    st.info("Faça login com Google para acessar sua área do cliente e ver seus relatórios salvos.")
    render_login_gate_block()


def resolve_calculate_access(
    *,
    clicked_calcular: bool,
    categoria_label: str,
    user_logged_in: bool,
    user_id: Optional[str],
    session_state: MutableMapping[str, Any],
) -> bool:
    run_free_calc_now = False

    if clicked_calcular:
        if categoria_label != "Residencial":
            st.info("Essa categoria ainda está em desenvolvimento. Use Residencial por enquanto.")
        elif not user_logged_in or not user_id:
            session_state["show_login_gate"] = True
            session_state["scroll_to_login_gate"] = True
            session_state["post_login_action"] = "calculate_viability"
        else:
            session_state["show_login_gate"] = False
            session_state["show_inline_payments"] = False
            session_state["scroll_to_item3"] = True
            run_free_calc_now = True

    if (
        session_state.get("post_login_action") == "calculate_viability"
        and user_logged_in
        and user_id
        and categoria_label == "Residencial"
    ):
        run_free_calc_now = True
        session_state["post_login_action"] = None
        session_state["show_login_gate"] = False
        session_state["scroll_to_item3"] = True

    return run_free_calc_now


def render_login_gate_if_needed(
    *,
    user_logged_in: bool,
    user_id: Optional[str],
    show_login_gate: bool,
) -> None:
    if show_login_gate and not (user_logged_in and user_id):
        render_login_gate_block()
        st.divider()
