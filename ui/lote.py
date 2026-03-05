from __future__ import annotations

from typing import Tuple

import streamlit as st


def render_lote_section() -> Tuple[float, float, float]:
    """
    2) Dados do lote

    Retorna SEMPRE (area_lote_usada_m2, area_terreo_pretendida_m2, area_permeavel_prevista_m2)

    Regras:
    - Sempre pede Testada e Profundidade primeiro.
    - Se "Terreno irregular" estiver DESMARCADO:
        area_lote = testada * profundidade (não mostra campo de área total)
    - Se "Terreno irregular" estiver MARCADO:
        mostra o campo "Área do lote (m²)" e usa essa área total (override)
        (avisa que não é área do térreo)
    - "Área pretendida no térreo": se 0, o relatório assume o máximo permitido pela zona.
    - "Área permeável prevista": aqui é apenas um valor-base (area_lote - area_terreo),
      os percentuais/TP são tratados no restante do sistema.
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
        # pt-BR formatting
        val = f"{area_calc:,.2f} m²".replace(",", "X").replace(".", ",").replace("X", ".")
        st.metric(label="", value=val)

    is_irregular = st.checkbox(
        "Terreno irregular",
        value=bool(st.session_state.get("lot_is_irregular") or False),
        key="lot_is_irregular",
    )

    lot_area_used = area_calc
    if is_irregular:
        st.info(
            "ℹ️ **Terreno irregular**: informe abaixo a **área total do lote** (não é a área do térreo). "
            "Neste modo, o sistema calcula apenas limites por **índices (TO/TP/IA)**; os cálculos por **recuos** "
            "não são feitos, pois exigem o polígono do lote (vértices/coordenadas) e a definição da frente."
        )
        lot_area_used = st.number_input(
            "Área do lote (m²)",
            min_value=0.0,
            value=float(st.session_state.get("lot_area_override_m2") or area_calc or 0.0),
            step=10.0,
            format="%.2f",
            key="lot_area_override_m2",
        )

    # manter no mesmo lugar
    st.checkbox("Lote de esquina", value=bool(st.session_state.get("lot_is_corner") or False), key="lot_is_corner")

    built_ground = st.number_input(
        "Área pretendida no térreo (m²) (se deixar 0, o relatório assume o máximo permitido)",
        min_value=0.0,
        value=float(st.session_state.get("built_ground_m2") or 0.0),
        step=5.0,
        format="%.2f",
        key="built_ground_m2",
    )

    if lot_area_used > 0 and built_ground > lot_area_used:
        st.warning("⚠️ A área pretendida no térreo está maior que a área total do lote.")

    permeable_area = max(float(lot_area_used or 0.0) - float(built_ground or 0.0), 0.0)
    return float(lot_area_used or 0.0), float(built_ground or 0.0), float(permeable_area or 0.0)
