from __future__ import annotations
import streamlit as st
def render_lote_section() -> dict:
    """Seção 2: Dados do lote.

    Salva tudo em st.session_state.lote para uso nos módulos (análise/relatório).
    """
    st.subheader("2) Dados do lote")

    lote = st.session_state.get("lote") or {}
    area0 = float(lote.get("area_m2") or 300.0)
    testada0 = float(lote.get("testada_m") or 10.0)
    prof0 = float(lote.get("profundidade_m") or 30.0)
    terreo0 = float(lote.get("area_terreo_m2") or 0.0)

    col1, col2, col3 = st.columns(3)
    with col1:
        lot_area = st.number_input("Área do lote (m²)", min_value=1.0, value=area0, step=10.0)
    with col2:
        testada = st.number_input("Largura (testada) (m)", min_value=1.0, value=testada0, step=0.5)
    with col3:
        profundidade = st.number_input("Profundidade (m)", min_value=1.0, value=prof0, step=0.5)

    built_ground = st.number_input(
        "Área pretendida no térreo (m²) (se deixar 0, o relatório assume o máximo permitido)",
        min_value=0.0,
        value=terreo0,
        step=5.0,
    )

    st.session_state.lote = {
        "area_m2": float(lot_area),
        "testada_m": float(testada),
        "profundidade_m": float(profundidade),
        "area_terreo_m2": float(built_ground),
    }
    return st.session_state.lote
