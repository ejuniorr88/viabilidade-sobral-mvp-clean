from __future__ import annotations

from typing import Tuple, Dict, Any

import streamlit as st


def _fmt_ptbr(v: float, dec: int = 2) -> str:
    s = f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s


def _ensure_calc() -> Dict[str, Any]:
    if "calc" not in st.session_state or not isinstance(st.session_state.calc, dict):
        st.session_state.calc = {}
    return st.session_state.calc


def render_lote_section() -> Tuple[float, float, float]:
    """
    Dados do lote

    Retorna:
    (area_lote_usada_m2, area_terreo_pretendida_m2, area_permeavel_prevista_m2)

    Regras mantidas:
    - Sempre pede Testada e Profundidade primeiro.
    - Se "Terreno irregular" estiver desmarcado:
      área do lote = testada * profundidade.
    - Se "Terreno irregular" estiver marcado:
      mostra campo "Área do lote (m²)" e usa esse valor.
    - Campo "Área pretendida no térreo (m²)" sempre existe.
    """

    calc = _ensure_calc()

    # --------------------------------------------------
    # Linha principal do lote
    # Comentário:
    # ajustada para ficar mais alinhada visualmente.
    # --------------------------------------------------
    c1, c2, c3 = st.columns([1, 1, 1.25], gap="medium")

    with c1:
        testada = st.number_input(
            "Largura (testada) (m)",
            min_value=0.0,
            value=float(calc.get("lot_testada_m", 10.0) or 10.0),
            step=0.1,
            format="%.2f",
            key="lot_testada_m_input",
        )

    with c2:
        profundidade = st.number_input(
            "Profundidade (m)",
            min_value=0.0,
            value=float(calc.get("lot_profundidade_m", 30.0) or 30.0),
            step=0.1,
            format="%.2f",
            key="lot_profundidade_m_input",
        )

    with c3:
        area_calc = float(testada) * float(profundidade)
        st.metric(
            "Área calculada (testada × profundidade)",
            f"{_fmt_ptbr(area_calc)} m²",
        )

    # --------------------------------------------------
    # Flags
    # --------------------------------------------------
    f1, f2 = st.columns(2, gap="medium")

    with f1:
        terreno_irregular = st.checkbox(
            "Terreno irregular",
            value=bool(calc.get("lot_irregular", False)),
            key="lot_irregular_checkbox",
        )

    with f2:
        lote_esquina = st.checkbox(
            "Lote de esquina",
            value=bool(calc.get("lot_is_corner", False)),
            key="lot_corner_checkbox",
        )

    # --------------------------------------------------
    # Área do lote quando irregular
    # --------------------------------------------------
    if terreno_irregular:
        area_lote = st.number_input(
            "Área do lote (m²)",
            min_value=0.0,
            value=float(calc.get("lot_area_m2", area_calc) or area_calc),
            step=1.0,
            format="%.2f",
            key="lot_area_m2_input",
        )
    else:
        area_lote = area_calc

    # --------------------------------------------------
    # Área pretendida no térreo
    # Comentário:
    # Tipo de projeto foi removido daqui porque agora
    # essa escolha já acontece em "Opções na Categoria".
    # --------------------------------------------------
    area_terreo_pretendida = st.number_input(
        "Área pretendida no térreo (m²) (se deixar 0, o relatório assume o máximo permitido)",
        min_value=0.0,
        value=float(calc.get("built_ground_m2", 0.0) or 0.0),
        step=1.0,
        format="%.2f",
        key="built_ground_m2_input",
    )

    # Compatibilidade com versões antigas
    calc["built_ground_m2"] = area_terreo_pretendida
    calc["built_ground_input_m2"] = area_terreo_pretendida

    # Persistência do lote
    calc["lot_testada_m"] = float(testada)
    calc["lot_profundidade_m"] = float(profundidade)
    calc["lot_irregular"] = bool(terreno_irregular)
    calc["lot_is_corner"] = bool(lote_esquina)
    calc["lot_area_m2"] = float(area_lote)

    # Área permeável prevista
    area_permeavel_prevista = float(calc.get("area_permeavel_prevista_m2", 0.0) or 0.0)
    calc["area_permeavel_prevista_m2"] = area_permeavel_prevista

    return float(area_lote), float(area_terreo_pretendida), float(area_permeavel_prevista)
