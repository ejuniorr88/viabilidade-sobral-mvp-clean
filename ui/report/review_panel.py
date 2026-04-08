from __future__ import annotations

from typing import Any, Dict

import streamlit as st


def _fmt_num(value: Any) -> str:
    try:
        return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "—"


def _pick_zone(calc: Dict[str, Any]) -> str:
    return str(calc.get("zone") or calc.get("zone_sigla") or calc.get("zone_lookup") or "—")


def _pick_street(calc: Dict[str, Any]) -> str:
    street = calc.get("street_name") or calc.get("via_name") or calc.get("road_name") or calc.get("logradouro")
    return str(street or "—")


def render_review_panel(*, calc: Dict[str, Any], session_snapshot: Dict[str, Any]) -> None:
    st.markdown("### Conferência dos dados do relatório")
    st.caption("Revise as informações abaixo antes de seguir para a emissão do relatório.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Zona do lote:** {_pick_zone(calc)}")
        st.markdown(f"**Rua/Via:** {_pick_street(calc)}")
    with c2:
        st.markdown(f"**Dimensões do terreno:** {_fmt_num(session_snapshot.get('lot_front_m'))} m × {_fmt_num(session_snapshot.get('lot_depth_m'))} m")
        st.markdown(f"**Área do lote:** {_fmt_num(session_snapshot.get('lot_area_m2'))} m²")

    area_pretendida = calc.get("built_ground_input_m2")
    if area_pretendida not in (None, "", 0, 0.0):
        st.markdown(f"**Área pretendida informada:** {_fmt_num(area_pretendida)} m²")
