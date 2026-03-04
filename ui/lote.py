from __future__ import annotations

from typing import Tuple

import streamlit as st


def render_lote_section() -> Tuple[float, float, float]:
    """Seção 2) Dados do lote

    IMPORTANTE: retorna SEMPRE 3 valores numéricos:
      (lot_area_m2, built_ground_m2, permeable_area_m2)

    Regras (Backup 04+):
    - Sempre exibe primeiro: Testada + Profundidade.
    - Área do lote padrão = (Testada × Profundidade).
    - Se marcar "Terreno irregular", aparece o campo "Área do lote (m²)" para informar a área TOTAL real.
    - Não exibe mais o campo "Área permeável prevista (m²)" na tela.
      A área permeável é assumida automaticamente como (Área do lote - Área do térreo).

    Campo novo (sem mexer no layout geral do app):
    - Checkbox "Lote de esquina" (usado apenas no relatório por enquanto).
    """
    st.subheader("2) Dados do lote")

    # 1) Sempre: Testada + Profundidade
    c2, c3 = st.columns(2)
    with c2:
        testada_m = st.number_input(
            "Largura (testada) (m)",
            min_value=0.0,
            value=float(st.session_state.get("lot_front_m", 10.0)),
            step=0.5,
            format="%.2f",
            key="lot_front_m",
        )
    with c3:
        profundidade_m = st.number_input(
            "Profundidade (m)",
            min_value=0.0,
            value=float(st.session_state.get("lot_depth_m", 30.0)),
            step=0.5,
            format="%.2f",
            key="lot_depth_m",
        )

    area_calc = float(testada_m) * float(profundidade_m)

    # 2) Terreno irregular (se marcado, usuário informa a área TOTAL do lote)
    terreno_irregular = st.checkbox(
        "Terreno irregular",
        value=bool(st.session_state.get("terreno_irregular", False)),
        help="Marque se o lote não for retangular e a área total não for (testada × profundidade).",
    )
    st.session_state["terreno_irregular"] = bool(terreno_irregular)

    if terreno_irregular:
        lot_area = st.number_input(
            "Área do lote (m²) — área total do terreno (irregular)",
            min_value=0.0,
            value=float(st.session_state.get("lot_area_irregular_m2", area_calc)),
            step=10.0,
            format="%.2f",
            key="lot_area_irregular_m2",
            help="Este campo é a área TOTAL do terreno. A área do térreo é informada abaixo.",
        )
        st.caption(f"Área calculada (testada × profundidade): {area_calc:,.2f} m²".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        lot_area = area_calc
        st.caption(f"Área do lote calculada automaticamente: {area_calc:,.2f} m² (testada × profundidade)".replace(",", "X").replace(".", ",").replace("X", "."))

    # 3) Lote de esquina (apenas para relatório por enquanto)
    is_corner = st.checkbox("Lote de esquina", value=bool(st.session_state.get("lote_esquina", False)))
    st.session_state["lote_esquina"] = bool(is_corner)
    calc = st.session_state.get("calc")
    if isinstance(calc, dict):
        calc["lote_esquina"] = bool(is_corner)

    # 4) Área pretendida no térreo
    built_ground = st.number_input(
        "Área pretendida no térreo (m²) (se deixar 0, o relatório assume o máximo permitido)",
        min_value=0.0,
        value=0.0,
        step=5.0,
        format="%.2f",
    )

    # Aviso simples para evitar confusão: térreo não pode ser maior que o lote
    if float(built_ground) > float(lot_area) and float(lot_area) > 0:
        st.warning("A área pretendida no térreo está maior que a área total do lote. Confira os valores.")

    permeable_area = max(0.0, float(lot_area) - float(built_ground))
    return float(lot_area), float(built_ground), float(permeable_area)
