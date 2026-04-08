from __future__ import annotations

from typing import Any, Dict

import streamlit as st


def _fmt_num(value: Any) -> str:
    try:
        return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "—"


def _fmt_dims(front: Any, depth: Any, area: Any, irregular: bool) -> str:
    if irregular:
        return f"Terreno irregular • área informada: {_fmt_num(area)} m²"
    if float(front or 0) > 0 and float(depth or 0) > 0:
        return f"{_fmt_num(front)} m × {_fmt_num(depth)} m • área: {_fmt_num(area)} m²"
    return f"Área do lote: {_fmt_num(area)} m²"


def build_review_summary(*, calc_ref: Dict[str, Any], session_snapshot: Dict[str, Any]) -> Dict[str, str]:
    area_pretendida = session_snapshot.get("built_ground_m2") or calc_ref.get("built_ground_m2") or calc_ref.get("built_ground_input_m2")
    has_area_pretendida = False
    try:
        has_area_pretendida = float(area_pretendida or 0) > 0
    except Exception:
        has_area_pretendida = False

    zone_value = (
        calc_ref.get("zone")
        or calc_ref.get("zone_label_raw")
        or calc_ref.get("zone_label")
        or calc_ref.get("zone_sigla")
        or "—"
    )
    street_value = calc_ref.get("via_nome") or calc_ref.get("street_name") or calc_ref.get("road_name") or calc_ref.get("logradouro") or "—"
    dimensions_value = _fmt_dims(
        session_snapshot.get("lot_front_m"),
        session_snapshot.get("lot_depth_m"),
        session_snapshot.get("lot_area_m2"),
        bool(session_snapshot.get("lot_is_irregular")),
    )
    return {
        "Zona do lote": str(zone_value),
        "Rua": str(street_value),
        "Dimensões do terreno": dimensions_value,
        "Área pretendida": f"{_fmt_num(area_pretendida)} m²" if has_area_pretendida else "Não informada",
    }


def render_review_panel(*, calc_ref: Dict[str, Any], session_snapshot: Dict[str, Any]) -> None:
    summary = build_review_summary(calc_ref=calc_ref, session_snapshot=session_snapshot)

    st.markdown("### Conferência dos dados")
    st.caption("Revise as informações abaixo antes de seguir para a geração do relatório.")

    col1, col2 = st.columns(2)
    items = list(summary.items())
    for idx, (label, value) in enumerate(items):
        target = col1 if idx % 2 == 0 else col2
        with target:
            st.markdown(f"**{label}**")
            st.write(value)
