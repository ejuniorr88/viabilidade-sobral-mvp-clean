from __future__ import annotations

from typing import Any, Callable

import streamlit as st


ClearRuntimeStateFn = Callable[..., Any]


def render_primary_actions(*, session_state, clear_report_runtime_state: ClearRuntimeStateFn) -> bool:
    """Renderiza o bloco principal de ações do fluxo sem acoplar o app.py.

    Mantém o layout consolidado: botão de gerar e botão de limpar abaixo do mapa.
    A limpeza segue exatamente o comportamento já consolidado do app.
    """

    btn_col1, btn_col2, btn_col3 = st.columns([1, 2.1, 1])
    with btn_col2:
        clicked_calcular = st.button(
            "🚀 GERAR ESTUDO DE VIABILIDADE",
            key="btn_calc",
            use_container_width=True,
        )

        limpar_tudo = st.button(
            "🗑️ LIMPAR TUDO",
            key="btn_clear_all",
            use_container_width=True,
        )

        if limpar_tudo:
            session_state.selected_lat = None
            session_state.selected_lon = None
            session_state.calc = {"use_type_code": session_state.calc.get("use_type_code", "RES_UNI")}
            clear_report_runtime_state(clear_last_calc_signature=True)
            session_state.free_calc_done = False
            session_state.show_login_gate = False
            session_state.scroll_to_login_gate = False
            session_state.scroll_to_item3 = False
            session_state.post_login_action = None
            session_state.show_inline_payments = False
            st.rerun()

    return clicked_calcular
