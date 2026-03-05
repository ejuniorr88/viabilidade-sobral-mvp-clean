from __future__ import annotations

from typing import Tuple

import streamlit as st


def _fmt_ptbr(v: float, dec: int = 2) -> str:
    s = f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s


def render_lote_section() -> Tuple[float, float, float]:
    """
    2) Dados do lote

    Retorna (area_lote_usada_m2, area_terreo_pretendida_m2, area_permeavel_prevista_m2)

    - Sempre pede Testada e Profundidade primeiro.
    - Se "Terreno irregular" estiver DESMARCADO: área do lote = testada * profundidade (não mostra campo de área).
    - Se "Terreno irregular" estiver MARCADO: mostra campo "Área do lote (m²)" (área total) e usa esse valor.
    """
    st.subheader("2) Dados do lote")

    c1, c2, c3 = st.columns(3)
    with c1:
        testada = st.number_input(
            "Largura (testada) (m)",
            min_value=0.0,
            value=float(st.session_state.get("lot_front_m") or 10.0),
            step=0.5,
            format="%.2f",
            key="lot_front_m",
        )
    with c2:
        profund = st.number_input(
            "Profundidade (m)",
            min_value=0.0,
            value=float(st.session_state.get("lot_depth_m") or 30.0),
            step=0.5,
            format="%.2f",
            key="lot_depth_m",
        )
    with c3:
        area_calc = float(testada or 0.0) * float(profund or 0.0)
        st.markdown("**Área calculada (testada × profundidade)**")
        st.metric(label="", value=f"{_fmt_ptbr(area_calc)} m²")

    is_irregular = st.checkbox(
        "Terreno irregular",
        value=bool(st.session_state.get("lot_is_irregular") or False),
        key="lot_is_irregular",
    )

    area_lote_usada = area_calc
    if is_irregular:
        st.info(
            "ℹ️ **Terreno irregular**: informe abaixo a **área total do lote** (não é a área do térreo). "
            "Neste modo, o sistema calcula apenas limites por **índices (TO/TP/IA)**; os cálculos por **recuos** "
            "não são feitos, pois exigem o polígono do lote (vértices/coordenadas) e a definição da frente."
        )
        area_lote_usada = st.number_input(
            "Área do lote (m²)",
            min_value=0.0,
            value=float(st.session_state.get("lot_area_override_m2") or area_calc or 0.0),
            step=10.0,
            format="%.2f",
            key="lot_area_override_m2",
        )

    st.checkbox("Lote de esquina", value=bool(st.session_state.get("lot_is_corner") or False), key="lot_is_corner")

    area_terreo = st.number_input(
        "Área pretendida no térreo (m²) (se deixar 0, o relatório assume o máximo permitido)",
        min_value=0.0,
        value=float(st.session_state.get("built_ground_m2") or 0.0),
        step=5.0,
        format="%.2f",
        key="built_ground_m2",
    )

    if area_lote_usada > 0 and area_terreo > area_lote_usada:
        st.warning("⚠️ A área pretendida no térreo está maior que a área total do lote.")

    area_permeavel_prevista = max(float(area_lote_usada or 0.0) - float(area_terreo or 0.0), 0.0)
    return float(area_lote_usada or 0.0), float(area_terreo or 0.0), float(area_permeavel_prevista or 0.0)
