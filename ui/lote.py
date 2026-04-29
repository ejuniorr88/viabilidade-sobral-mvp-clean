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


def _default_midblock(calc: Dict[str, Any]) -> bool:
    if "lot_is_midblock" in calc:
        return bool(calc.get("lot_is_midblock"))
    return not bool(calc.get("lot_is_corner", False))


def _activate_midblock() -> None:
    st.session_state["lot_midblock_checkbox"] = True
    st.session_state["lot_corner_checkbox"] = False


def _activate_corner() -> None:
    st.session_state["lot_corner_checkbox"] = True
    st.session_state["lot_midblock_checkbox"] = False


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

    # ======================================================
    # Campos empilhados para evitar desalinhamento na sidebar
    # ======================================================
    testada = st.number_input(
        "Testada / Frente (m):",
        min_value=0.0,
        value=float(calc.get("lot_testada_m", 10.0) or 10.0),
        step=0.1,
        format="%.2f",
        key="lot_testada_m_input",
    )

    profundidade = st.number_input(
        "Profundidade / Lateral (m):",
        min_value=0.0,
        value=float(calc.get("lot_profundidade_m", 30.0) or 30.0),
        step=0.1,
        format="%.2f",
        key="lot_profundidade_m_input",
    )

    area_calc = float(testada) * float(profundidade)
    st.caption(f"Área calculada: {_fmt_ptbr(area_calc)} m²")

    # ======================================================
    # Checkboxes alinhados
    # ======================================================
    if "lot_midblock_checkbox" not in st.session_state:
        st.session_state["lot_midblock_checkbox"] = _default_midblock(calc)
    if "lot_corner_checkbox" not in st.session_state:
        st.session_state["lot_corner_checkbox"] = bool(calc.get("lot_is_corner", False))

    f1, f2 = st.columns(2, gap="small")

    with f1:
        terreno_irregular = st.checkbox(
            "Terreno irregular",
            value=bool(calc.get("lot_irregular", False)),
            key="lot_irregular_checkbox",
        )

    with f2:
        st.checkbox(
            "Lote meio de quadra",
            key="lot_midblock_checkbox",
            on_change=_activate_midblock,
        )

    f3, f4 = st.columns(2, gap="small")
    with f3:
        st.checkbox(
            "Lote de esquina",
            key="lot_corner_checkbox",
            on_change=_activate_corner,
        )

    lote_meio_quadra = bool(st.session_state.get("lot_midblock_checkbox", True))
    lote_esquina = bool(st.session_state.get("lot_corner_checkbox", False))

    if lote_meio_quadra and lote_esquina:
        lote_meio_quadra = False
        lote_esquina = True
        st.session_state["lot_midblock_checkbox"] = False
        st.session_state["lot_corner_checkbox"] = True
    elif not lote_meio_quadra and not lote_esquina:
        lote_meio_quadra = True
        lote_esquina = False
        st.session_state["lot_midblock_checkbox"] = True
        st.session_state["lot_corner_checkbox"] = False

    # ======================================================
    # Área do lote quando irregular
    # ======================================================
    if terreno_irregular:
        area_lote = st.number_input(
            "Área do lote (m²):",
            min_value=0.0,
            value=float(calc.get("lot_area_m2", area_calc) or area_calc),
            step=1.0,
            format="%.2f",
            key="lot_area_m2_input",
        )
    else:
        area_lote = area_calc

    # ======================================================
    # Campo final alinhado
    # ======================================================
    area_terreo_pretendida = st.number_input(
        "Área Construída Pretendida no Térreo (m²):",
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
    calc["lot_is_midblock"] = bool(lote_meio_quadra)
    calc["lot_area_m2"] = float(area_lote)

    st.session_state["lot_is_corner"] = bool(lote_esquina)
    st.session_state["lot_is_midblock"] = bool(lote_meio_quadra)
    st.session_state["lot_is_irregular"] = bool(terreno_irregular)
    st.session_state["lot_front_m"] = float(testada)
    st.session_state["lot_depth_m"] = float(profundidade)

    # Área permeável prevista
    area_permeavel_prevista = float(calc.get("area_permeavel_prevista_m2", 0.0) or 0.0)
    calc["area_permeavel_prevista_m2"] = area_permeavel_prevista

    return float(area_lote), float(area_terreo_pretendida), float(area_permeavel_prevista)
