from __future__ import annotations

from typing import Any, Dict, Tuple

import streamlit as st


UseSelectorResult = Tuple[str, str, str, str]


RESIDENTIAL_OPTIONS: Dict[str, Tuple[str, str]] = {
    "Residencial Unifamiliar (Casa)": ("RES_UNI", ""),
    "Multifamiliar R2.1 (2 unidades no mesmo lote)": ("RES_MULTI_R21", "R21"),
    "Multifamiliar R2.2 (condomínio horizontal com via interna)": ("RES_MULTI_R22", "R22"),
    "Multifamiliar R3 (condomínio vertical / prédio)": ("RES_MULTI_R3", "R3"),
}


def render_use_selector(session_state: Any) -> UseSelectorResult:
    """Renderiza a barra lateral inicial consolidada do fluxo.

    Escopo intencionalmente limitado ao bloco visual de:
    - 1. Escolha o Uso
    - 2. Busca Direta

    Mantém a persistência mínima já consolidada em session_state.calc,
    sem tocar em mapa, lote, localização, índices ou relatório.
    """

    st.markdown("### 📋 1. Escolha o Uso")

    categoria_label = st.selectbox(
        "Categoria:",
        options=[
            "Residencial",
            "Comercial (Em breve)",
            "Serviço (Em breve)",
            "Saúde/Educação (Em breve)",
        ],
        index=0,
        key="vf_categoria",
    )

    selected_use_label = st.selectbox(
        "Opções na Categoria:",
        options=list(RESIDENTIAL_OPTIONS.keys()),
        index=0,
        key="vf_residential_option",
        disabled=(categoria_label != "Residencial"),
    )

    selected_use_code, selected_multi_tipo = RESIDENTIAL_OPTIONS.get(selected_use_label, ("RES_UNI", ""))
    session_state.calc["use_type_code"] = selected_use_code

    if selected_use_code.startswith("RES_MULTI_"):
        session_state.calc["project_mode"] = "GUIA_FASE_1"
        session_state.calc["multi_tipo"] = selected_multi_tipo
    else:
        session_state.calc.pop("project_mode", None)
        session_state.calc.pop("multi_tipo", None)

    if categoria_label != "Residencial":
        st.caption("Essa categoria ficará disponível em breve.")

    st.markdown('<div class="vf-side-divider"></div>', unsafe_allow_html=True)

    st.markdown("### 🔎 2. Busca Direta")
    st.text_input(
        "Ou digite para pesquisar:",
        value="Em breve",
        disabled=True,
        key="vf_busca_direta",
    )
    st.caption("A busca direta ficará disponível em breve.")

    st.markdown('<div class="vf-side-divider"></div>', unsafe_allow_html=True)

    return categoria_label, selected_use_label, selected_use_code, selected_multi_tipo
