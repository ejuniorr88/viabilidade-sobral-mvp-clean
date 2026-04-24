from __future__ import annotations

"""Renderer compartilhado dos dados iniciais da consulta.

Este módulo centraliza os campos que antes ficavam diretamente no `app.py`:
- 1. Escolha o Uso
- 2. Busca Direta
- 3. Dados do Lote

A intenção é permitir que o mesmo formulário seja usado na sidebar do desktop e,
no mobile, dentro do fluxo principal abaixo do mapa, sem duplicar regra de negócio.
"""

from typing import Any, Tuple

import streamlit as st

from ui.flow.use_selector import render_use_selector
from ui.lot.inputs import render_lot_inputs


ConsultationFormResult = Tuple[str, str, str, str, float, float, float]


def render_consultation_form(session_state: Any) -> ConsultationFormResult:
    """Renderiza o formulário consolidado da consulta e retorna seus valores.

    Não toca em autenticação, pagamentos, crédito, mapa, regras urbanísticas,
    relatório ou PDF. Apenas reutiliza os componentes já consolidados de uso e
    dados do lote.
    """

    categoria_label, selected_use_label, selected_use_code, selected_multi_tipo = render_use_selector(session_state)
    session_state.calc["use_type_code"] = selected_use_code

    st.markdown("### 📐 3. Dados do Lote")
    st.caption("Mantido o bloco funcional já consolidado, incluindo a lógica de terreno irregular.")

    lot_area, built_ground, permeable_area = render_lot_inputs()

    return (
        categoria_label,
        selected_use_label,
        selected_use_code,
        selected_multi_tipo,
        lot_area,
        built_ground,
        permeable_area,
    )
