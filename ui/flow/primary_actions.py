from __future__ import annotations

from typing import Any, Callable

import streamlit as st


ClearRuntimeStateFn = Callable[..., Any]


def _perform_clear_all(*, session_state, clear_report_runtime_state: ClearRuntimeStateFn) -> None:
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
    session_state.confirm_clear_all = False
    st.rerun()


def _has_generated_report(session_state) -> bool:
    return bool(
        session_state.get("report_snapshot_signature")
        or session_state.get("last_generated_pdf_bytes")
        or session_state.get("report_unlocked")
        or session_state.get("last_saved_report_signature")
    )


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
            if _has_generated_report(session_state):
                session_state.confirm_clear_all = True
                st.rerun()
            _perform_clear_all(
                session_state=session_state,
                clear_report_runtime_state=clear_report_runtime_state,
            )

        if session_state.get("confirm_clear_all") and _has_generated_report(session_state):
            st.warning(
                "Você realmente deseja limpar todos os dados deste estudo? "
                "O relatório já gerado continuará armazenado na Área do Cliente para consulta posterior."
            )
            confirm_col1, confirm_col2 = st.columns(2)
            with confirm_col1:
                confirm_clear_yes = st.button(
                    "Sim, limpar tudo",
                    key="btn_confirm_clear_all_yes",
                    use_container_width=True,
                )
            with confirm_col2:
                confirm_clear_no = st.button(
                    "Cancelar",
                    key="btn_confirm_clear_all_no",
                    use_container_width=True,
                )

            if confirm_clear_yes:
                _perform_clear_all(
                    session_state=session_state,
                    clear_report_runtime_state=clear_report_runtime_state,
                )
            if confirm_clear_no:
                session_state.confirm_clear_all = False
                st.rerun()

    return clicked_calcular
