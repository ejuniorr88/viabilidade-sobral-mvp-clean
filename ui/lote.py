from __future__ import annotations

import streamlit as st


def render_lote_section():
    """Renderiza o bloco 2) Dados do lote e retorna os valores.

    Mantém o mesmo layout (3 colunas) e mesmos defaults.
    Não toca em Supabase, ruas, zona, nem cálculos.
    """
    st.subheader("2) Dados do lote")

    col1, col2, col3 = st.columns(3)
    with col1:
        lot_area = st.number_input("Área do lote (m²)", min_value=1.0, value=300.0, step=10.0)
    with col2:
        testada = st.number_input("Largura (testada) (m)", min_value=1.0, value=10.0, step=0.5)
    with col3:
        profundidade = st.number_input("Profundidade (m)", min_value=1.0, value=30.0, step=0.5)

    built_ground = st.number_input("Área pretendida no térreo (m²)", min_value=0.0, value=0.0, step=5.0)

    return lot_area, testada, profundidade, built_ground
