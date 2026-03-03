from __future__ import annotations

from typing import Dict, Any
import streamlit as st


def render_lote_section() -> Dict[str, Any]:
    """
    2) Dados do lote

    Retorna sempre um dict com:
        lot_area_m2
        built_ground_m2
        permeable_area_m2
    """

    st.subheader("2) Dados do lote")

    col1, col2, col3 = st.columns(3)

    with col1:
        lot_area = st.number_input(
            "Área do lote (m²)",
            min_value=0.0,
            value=300.0,
            step=1.0,
            format="%.2f",
            key="lot_area_input",
        )

    with col2:
        largura = st.number_input(
            "Largura (testada) (m)",
            min_value=0.0,
            value=10.0,
            step=0.1,
            format="%.2f",
            key="lot_width_input",
        )

    with col3:
        profundidade = st.number_input(
            "Profundidade (m)",
            min_value=0.0,
            value=30.0,
            step=0.1,
            format="%.2f",
            key="lot_depth_input",
        )

    built_ground = st.number_input(
        "Área pretendida no térreo (m²) (se deixar 0, o relatório assume o máximo permitido)",
        min_value=0.0,
        value=0.0,
        step=1.0,
        format="%.2f",
        key="built_ground_input",
    )

    permeable_area = st.number_input(
        "Área permeável prevista (m²)",
        min_value=0.0,
        value=0.0,
        step=1.0,
        format="%.2f",
        key="permeable_area_input",
    )

    return {
        "lot_area_m2": lot_area,
        "built_ground_m2": built_ground,
        "permeable_area_m2": permeable_area,
        "width_m": largura,
        "depth_m": profundidade,
    }
