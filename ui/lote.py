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

    terreno_irregular_pre = bool(
        st.session_state.get(
            "lot_irregular_checkbox",
            calc.get("lot_irregular", calc.get("lot_is_irregular", False)),
        )
    )

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
        disabled=terreno_irregular_pre,
        help="Em terreno irregular, testada e profundidade não entram no cálculo.",
    )

    profundidade = st.number_input(
        "Profundidade / Lateral (m):",
        min_value=0.0,
        value=float(calc.get("lot_profundidade_m", 30.0) or 30.0),
        step=0.1,
        format="%.2f",
        key="lot_profundidade_m_input",
        disabled=terreno_irregular_pre,
        help="Em terreno irregular, testada e profundidade não entram no cálculo.",
    )

    area_calc = float(testada) * float(profundidade)
    if terreno_irregular_pre:
        st.caption("Terreno irregular: testada e profundidade serão desconsideradas. Informe a área total do lote abaixo.")
    else:
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
        if terreno_irregular:
            st.checkbox(
                "Lote meio de quadra",
                value=False,
                key="lot_midblock_checkbox_disabled_irregular",
                disabled=True,
                help="Para terreno irregular, os cálculos usam apenas a área total informada.",
            )
        else:
            st.checkbox(
                "Lote meio de quadra",
                key="lot_midblock_checkbox",
                on_change=_activate_midblock,
            )

    f3, f4 = st.columns(2, gap="small")
    with f3:
        if terreno_irregular:
            st.checkbox(
                "Lote de esquina",
                value=False,
                key="lot_corner_checkbox_disabled_irregular",
                disabled=True,
                help="Para terreno irregular, os cálculos usam apenas a área total informada.",
            )
        else:
            st.checkbox(
                "Lote de esquina",
                key="lot_corner_checkbox",
                on_change=_activate_corner,
            )

    if terreno_irregular:
        # Terreno irregular não deve combinar com meio de quadra nem esquina.
        # A regra é aplicada apenas nas variáveis de cálculo, sem reescrever
        # st.session_state das chaves dos widgets já renderizados.
        lote_meio_quadra = False
        lote_esquina = False
    else:
        lote_meio_quadra = bool(st.session_state.get("lot_midblock_checkbox", True))
        lote_esquina = bool(st.session_state.get("lot_corner_checkbox", False))

        # Proteção lógica sem alterar session_state dos widgets depois da renderização.
        # Se algum estado antigo vier inconsistente, a regra local corrige o cálculo,
        # mas não tenta modificar a chave do checkbox no mesmo ciclo do Streamlit.
        if lote_meio_quadra and lote_esquina:
            lote_meio_quadra = False
            lote_esquina = True
        elif not lote_meio_quadra and not lote_esquina:
            lote_meio_quadra = True
            lote_esquina = False

    # ======================================================
    # Área do lote quando irregular
    # ======================================================
    if terreno_irregular:
        area_lote = st.number_input(
            "Área total do lote irregular (m²):",
            min_value=0.0,
            value=float(calc.get("lot_area_m2", area_calc) or area_calc),
            step=1.0,
            format="%.2f",
            key="lot_area_m2_input",
            help="Use a área total da matrícula ou do levantamento. Testada e profundidade não serão usadas no cálculo.",
        )
        st.info(
            "Por se tratar de terreno irregular, os cálculos de TO, TP e IA usarão somente a área total informada. "
            "A implantação deve ser conferida em projeto conforme a geometria real do lote."
        )
    else:
        area_lote = area_calc

    # ======================================================
    # Campo final alinhado
    # ======================================================
    area_terreo_pretendida = st.number_input(
        "Área Construída Pretendida no Térreo (m²):(Opcional)",
        min_value=0.0,
        value=float(calc.get("built_ground_m2", 0.0) or 0.0),
        step=1.0,
        format="%.2f",
        key="built_ground_m2_input",
    )

    st.markdown(
        """
        <div style="font-size: 16px; color: #555; line-height: 1.4; margin-top: -6px; margin-bottom: 6px;">
            **Observação: Se ainda não souber a área construída no térreo, deixe 0 para calcular o potencial máximo permitido.**
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Compatibilidade com versões antigas
    calc["built_ground_m2"] = area_terreo_pretendida
    calc["built_ground_input_m2"] = area_terreo_pretendida

    if terreno_irregular:
        # Neutraliza dimensões retangulares apenas nos dados finais usados por
        # cálculo/relatório. Não altera o session_state dos widgets já renderizados.
        testada_final = 0.0
        profundidade_final = 0.0
        tipo_lote = "Terreno irregular"
    else:
        testada_final = float(testada)
        profundidade_final = float(profundidade)
        tipo_lote = "Esquina" if lote_esquina else "Meio de quadra"

    # Persistência do lote
    calc["lot_testada_m"] = float(testada_final)
    calc["lot_profundidade_m"] = float(profundidade_final)
    calc["lot_front_m"] = float(testada_final)
    calc["lot_depth_m"] = float(profundidade_final)
    calc["lot_irregular"] = bool(terreno_irregular)
    calc["lot_is_irregular"] = bool(terreno_irregular)
    calc["lot_is_corner"] = bool(lote_esquina)
    calc["lot_is_midblock"] = bool(lote_meio_quadra)
    calc["lot_type_label"] = tipo_lote
    calc["lot_dimensions_label"] = (
        "Terreno irregular – cálculo pela área total informada"
        if terreno_irregular
        else f"{_fmt_ptbr(testada_final)} m × {_fmt_ptbr(profundidade_final)} m"
    )
    calc["lot_area_m2"] = float(area_lote)

    st.session_state["lot_is_corner"] = bool(lote_esquina)
    st.session_state["lot_is_midblock"] = bool(lote_meio_quadra)
    st.session_state["lot_is_irregular"] = bool(terreno_irregular)
    st.session_state["lot_type_label"] = tipo_lote
    st.session_state["lot_dimensions_label"] = calc["lot_dimensions_label"]
    st.session_state["lot_area_m2"] = float(area_lote)
    st.session_state["lot_front_m"] = float(testada_final)
    st.session_state["lot_depth_m"] = float(profundidade_final)

    # Área permeável prevista
    area_permeavel_prevista = float(calc.get("area_permeavel_prevista_m2", 0.0) or 0.0)
    calc["area_permeavel_prevista_m2"] = area_permeavel_prevista

    return float(area_lote), float(area_terreo_pretendida), float(area_permeavel_prevista)
