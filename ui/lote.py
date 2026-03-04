from __future__ import annotations

from typing import Tuple

import streamlit as st


def render_lote_section() -> Tuple[float, float, float]:
    """Seção 2) Dados do lote

    IMPORTANTe: retorna SEMPRE 3 valores numéricos:
      (lot_area_m2, built_ground_m2, permeable_area_m2)

    - built_ground_m2: área pretendida no térreo.
    - permeable_area_m2: calculada automaticamente (lot_area - built_ground),
      mas o usuário pode ajustar se quiser (mantive o campo para compat).
    """
    st.subheader("2) Dados do lote")

    c1, c2, c3 = st.columns(3)
    with c1:
        lot_area = st.number_input("Área do lote (m²)", min_value=0.0, value=300.0, step=10.0, format="%.2f")
    with c2:
        st.number_input("Largura (testada) (m)", min_value=0.0, value=10.0, step=0.5, format="%.2f", key="lot_front_m")
    with c3:
        st.number_input("Profundidade (m)", min_value=0.0, value=30.0, step=0.5, format="%.2f", key="lot_depth_m")

    st.checkbox("Lote de esquina", key="lot_is_corner", help="Marque se o lote tiver duas frentes (esquina).")

    built_ground = st.number_input(
        "Área pretendida no térreo (m²) (se deixar 0, o relatório assume o máximo permitido)",
        min_value=0.0,
        value=0.0,
        step=5.0,
        format="%.2f",
    )

    # Permeável default = lote - térreo
    default_perm = max(0.0, float(lot_area) - float(built_ground))

    # Mantive o campo para não quebrar layout antigo. Se quiser remover depois, eu removo.
    permeable_area = st.number_input(
        "Área permeável prevista (m²)",
        min_value=0.0,
        value=float(default_perm),
        step=5.0,
        format="%.2f",
        help="Se não informar, usamos (Área do lote - Área do térreo).",
    )

    return float(lot_area), float(built_ground), float(permeable_area)
