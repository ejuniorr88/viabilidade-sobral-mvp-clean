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
    2) Dados do lote

    Retorna (area_lote_usada_m2, area_terreo_pretendida_m2, area_permeavel_prevista_m2)

    Regras (mantidas):
    - Sempre pede Testada e Profundidade primeiro.
    - Se "Terreno irregular" estiver DESMARCADO: área do lote = testada * profundidade (não mostra campo de área).
    - Se "Terreno irregular" estiver MARCADO: mostra campo "Área do lote (m²)" (área total) e usa esse valor.
    - Campo "Área pretendida no térreo (m²)" sempre existe (se 0, o relatório pode assumir máximo permitido).
    """

    st.subheader("2) Dados do lote")

    calc = _ensure_calc()

    # -------------------------
    # Medidas básicas do lote
    # -------------------------
    c1, c2, c3 = st.columns(3)
    with c1:
        testada = st.number_input("Largura (testada) (m)", min_value=0.0, value=float(calc.get("lot_testada_m", 10.0) or 10.0), step=0.1, format="%.2f")
    with c2:
        profundidade = st.number_input("Profundidade (m)", min_value=0.0, value=float(calc.get("lot_profundidade_m", 30.0) or 30.0), step=0.1, format="%.2f")
    with c3:
        area_calc = float(testada) * float(profundidade)
        st.metric("Área calculada (testada × profundidade)", f"{_fmt_ptbr(area_calc)} m²")

    # Flags
    terreno_irregular = st.checkbox("Terreno irregular", value=bool(calc.get("lot_irregular", False)))
    lote_esquina = st.checkbox("Lote de esquina", value=bool(calc.get("lot_is_corner", False)))

    # Área do lote usada
    if terreno_irregular:
        area_lote = st.number_input("Área do lote (m²)", min_value=0.0, value=float(calc.get("lot_area_m2", area_calc) or area_calc), step=1.0, format="%.2f")
    else:
        area_lote = area_calc

    # -------------------------
    # Tipo de projeto (com descrições curtas)
    # -------------------------
    st.markdown("**Tipo de projeto**")

    # label -> value
    options = [
        ("Residencial Unifamiliar (RES_UNI) — 1 casa no lote.", "RES_UNI", ""),
        ("Multifamiliar R2.1 (RES_MULTI_R21) — 2 unidades no mesmo lote.", "RES_MULTI_R21", "R21"),
        ("Multifamiliar R2.2 (RES_MULTI_R22) — condomínio horizontal com via interna.", "RES_MULTI_R22", "R22"),
        ("Multifamiliar R3 (RES_MULTI_R3) — condomínio vertical (prédio).", "RES_MULTI_R3", "R3"),
    ]

    current_code = (calc.get("use_type_code") or "RES_UNI").upper()
    # fallback para o primeiro se não reconhecer
    idx = next((i for i, (_, code, _) in enumerate(options) if code == current_code), 0)

    chosen_label = st.selectbox(
        "Tipo de projeto",
        [o[0] for o in options],
        index=idx,
        label_visibility="collapsed",
    )
    chosen = next(o for o in options if o[0] == chosen_label)
    use_type_code = chosen[1]
    multi_tipo = chosen[2]

    # Modo do multifamiliar (por enquanto: só Fase 1)
    if use_type_code.startswith("RES_MULTI_"):
        st.markdown("**Modo do multifamiliar**")
        st.selectbox(
            "Modo do multifamiliar",
            ["Fase 1 — Guia do Projetista"],
            index=0,
            disabled=True,
            label_visibility="collapsed",
        )
        calc["project_mode"] = "GUIA_FASE_1"
        calc["multi_tipo"] = multi_tipo
    else:
        calc.pop("project_mode", None)
        calc.pop("multi_tipo", None)

    calc["use_type_code"] = use_type_code

    # -------------------------
    # Área pretendida no térreo
    # -------------------------
    area_terreo_pretendida = st.number_input(
        "Área pretendida no térreo (m²) (se deixar 0, o relatório assume o máximo permitido)",
        min_value=0.0,
        value=float(calc.get("built_ground_m2", 0.0) or 0.0),
        step=1.0,
        format="%.2f",
    )

    # Compatibilidade com versões antigas
    calc["built_ground_m2"] = area_terreo_pretendida
    calc["built_ground_input_m2"] = area_terreo_pretendida

    # Persistir lote
    calc["lot_testada_m"] = float(testada)
    calc["lot_profundidade_m"] = float(profundidade)
    calc["lot_irregular"] = bool(terreno_irregular)
    calc["lot_is_corner"] = bool(lote_esquina)
    calc["lot_area_m2"] = float(area_lote)

    # Área permeável prevista (fase 1: não calcula, deixa como 0 para não inventar)
    area_permeavel_prevista = float(calc.get("area_permeavel_prevista_m2", 0.0) or 0.0)
    calc["area_permeavel_prevista_m2"] = area_permeavel_prevista

    return float(area_lote), float(area_terreo_pretendida), float(area_permeavel_prevista)
