from __future__ import annotations

from typing import Tuple

import streamlit as st


def render_lote_section() -> Tuple[float, float, float]:
    """Seção 2) Dados do lote

    IMPORTANTE: retorna SEMPRE 3 valores numéricos:
      (lot_area_m2, built_ground_m2, permeable_area_m2)

    Regras:
    - Por padrão (terreno regular), a área do lote é calculada como:
        Área = Testada * Profundidade
      e usada em todos os cálculos/relatório.
    - Se marcar "Terreno irregular", aparece o campo "Área do lote (m²)" e
      o valor informado passa a ser usado em todos os cálculos/relatório.

    Observação de layout:
    - Mantém os mesmos campos do MVP (sem reintroduzir "Área permeável prevista (m²)" na tela).
    - Checkbox "Lote de esquina" permanece logo abaixo de Testada/Profundidade (usado apenas no relatório por enquanto).
    """
    st.subheader("2) Dados do lote")

    # 1) Entrada principal: Testada + Profundidade (sempre visíveis)
    c1, c2, c3 = st.columns(3)
    with c1:
        testada = st.number_input(
            "Largura (testada) (m)",
            min_value=0.0,
            value=float(st.session_state.get("lot_front_m", 10.0)),
            step=0.5,
            format="%.2f",
            key="lot_front_m",
        )
    with c2:
        profundidade = st.number_input(
            "Profundidade (m)",
            min_value=0.0,
            value=float(st.session_state.get("lot_depth_m", 30.0)),
            step=0.5,
            format="%.2f",
            key="lot_depth_m",
        )
    with c3:
        terreno_irregular = st.checkbox(
            "Terreno irregular",
            value=bool(st.session_state.get("terreno_irregular", False)),
            help="Marque se a área real do lote NÃO for simplesmente testada × profundidade.",
        )
        st.session_state["terreno_irregular"] = bool(terreno_irregular)

    # 2) Área do lote: calculada (regular) OU informada (irregular)
    area_calc = float(testada) * float(profundidade)

    lot_area_informada = float(st.session_state.get("lot_area_m2", area_calc))
    if terreno_irregular:
        lot_area_informada = st.number_input(
            "Área do lote (m²)",
            min_value=0.0,
            value=float(lot_area_informada),
            step=10.0,
            format="%.2f",
            key="lot_area_m2",
            help="Informe a área real do lote (ex.: terreno irregular, formato não retangular, etc.).",
        )
        lot_area = float(lot_area_informada)
    else:
        # terreno regular: usa a área calculada
        lot_area = float(area_calc)
        # mantém um espelho no estado (útil para relatório/debug sem abrir campo)
        st.session_state["lot_area_m2"] = float(lot_area)

    # texto discreto para o usuário entender qual área está sendo usada (não muda layout)
    st.caption(f"Área do lote usada nos cálculos: {lot_area:,.2f} m²".replace(",", "X").replace(".", ",").replace("X", "."))

    # novo: apenas para relatório (sem validação por enquanto)
    is_corner = st.checkbox("Lote de esquina", value=bool(st.session_state.get("lote_esquina", False)))
    st.session_state["lote_esquina"] = bool(is_corner)
    # também salva no calc se existir (para o relatório não depender de outro estado)
    calc = st.session_state.get("calc")
    if isinstance(calc, dict):
        calc["lote_esquina"] = bool(is_corner)

    # 3) Área pretendida no térreo (como já estava)
    built_ground = st.number_input(
        "Área pretendida no térreo (m²) (se deixar 0, o relatório assume o máximo permitido)",
        min_value=0.0,
        value=0.0,
        step=5.0,
        format="%.2f",
    )

    # Permeável default = lote - térreo (sem input na UI)
    permeable_area = max(0.0, float(lot_area) - float(built_ground))

    return float(lot_area), float(built_ground), float(permeable_area)
