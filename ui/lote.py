from __future__ import annotations

from typing import Tuple

import streamlit as st


def render_lote_section() -> Tuple[float, float, float]:
    """Seção 2) Dados do lote

    IMPORTANTE: retorna SEMPRE 3 valores numéricos:
      (lot_area_m2, built_ground_m2, permeable_area_m2)

    Observação de layout:
    - Mantém os mesmos campos principais do MVP.
    - NÃO exibe mais o campo "Área permeável prevista (m²)" na tela.
      A área permeável é assumida automaticamente como (Área do lote - Área do térreo).

    Campo novo (sem mexer no layout existente):
    - Checkbox "Lote de esquina" logo abaixo de Testada/Profundidade (usado apenas no relatório por enquanto).
    """
    st.subheader("2) Dados do lote")

    c1, c2, c3 = st.columns(3)
    with c1:
        lot_area = st.number_input("Área do lote (m²)", min_value=0.0, value=300.0, step=10.0, format="%.2f")
    with c2:
        st.number_input("Largura (testada) (m)", min_value=0.0, value=10.0, step=0.5, format="%.2f", key="lot_front_m")
    with c3:
        st.number_input("Profundidade (m)", min_value=0.0, value=30.0, step=0.5, format="%.2f", key="lot_depth_m")

    # novo: apenas para relatório (sem validação por enquanto)
    is_corner = st.checkbox("Lote de esquina", value=bool(st.session_state.get("lote_esquina", False)))
    st.session_state["lote_esquina"] = bool(is_corner)
    # também salva no calc se existir (para o relatório não depender de outro estado)
    calc = st.session_state.get("calc")
    if isinstance(calc, dict):
        calc["lote_esquina"] = bool(is_corner)

    built_ground = st.number_input(
        "Área pretendida no térreo (m²) (se deixar 0, o relatório assume o máximo permitido)",
        min_value=0.0,
        value=0.0,
        step=5.0,
        format="%.2f",
    )

    # Permeável default = lote - térreo (sem input na UI)
    permeable_area = max(0.0, float(lot_area) - float(built_ground))

    return float(lot_area), float(built_ground), float(permeable_area)
