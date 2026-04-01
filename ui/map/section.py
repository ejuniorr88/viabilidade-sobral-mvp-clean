from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from ui.mapa import render_mapa_section as _render_mapa_core


def render_mapa_section(zones_gj: Dict[str, Any]) -> int:
    st.markdown(
        '<div class="vf-section-title">📍 Selecione o lote no mapa:</div>',
        unsafe_allow_html=True,
    )
    return _render_mapa_core(zones_gj)


# Alias nominal para a arquitetura nova, mantendo compatibilidade com o nome antigo.
def render_map_section(zones_gj: Dict[str, Any]) -> int:
    return render_mapa_section(zones_gj)
