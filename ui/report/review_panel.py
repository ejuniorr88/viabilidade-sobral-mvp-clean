from __future__ import annotations

from typing import Any, Dict

import streamlit as st


_CARD_CSS = """
<style>
.report-review-card {
    background: linear-gradient(180deg, #f8fbff 0%, #f2f7ff 100%);
    border: 1px solid #dbe7f6;
    border-radius: 16px;
    padding: 1.15rem 1.2rem 1rem 1.2rem;
    margin: 0.4rem 0 1rem 0;
    box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
}
.report-review-card h3 {
    margin: 0 0 0.2rem 0;
    font-size: 1.05rem;
    font-weight: 700;
    color: #183153;
}
.report-review-card p {
    margin: 0;
    color: #5b6472;
    font-size: 0.95rem;
}
.report-review-divider {
    height: 1px;
    background: #e7eef8;
    margin: 0.95rem 0 0.85rem 0;
}
.review-item {
    background: rgba(255, 255, 255, 0.72);
    border: 1px solid #e6edf7;
    border-radius: 12px;
    padding: 0.85rem 0.95rem;
    min-height: 88px;
}
.review-item-label {
    display: block;
    font-size: 0.84rem;
    font-weight: 600;
    color: #5b6472;
    margin-bottom: 0.28rem;
}
.review-item-value {
    display: block;
    font-size: 1rem;
    font-weight: 700;
    color: #182230;
    line-height: 1.4;
    word-break: break-word;
}
.review-highlight {
    margin-top: 0.8rem;
    background: #ffffff;
    border: 1px solid #e6edf7;
    border-radius: 12px;
    padding: 0.85rem 0.95rem;
}
.review-highlight .review-item-label {
    margin-bottom: 0.15rem;
}
</style>
"""


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


def _render_item(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="review-item">
            <span class="review-item-label">{label}</span>
            <span class="review-item-value">{value}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_review_panel(*, calc: Dict[str, Any], session_snapshot: Dict[str, Any]) -> None:
    st.markdown(_CARD_CSS, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="report-review-card">
            <h3>Conferência dos dados do relatório</h3>
            <p>Revise as informações abaixo antes de seguir para a emissão do relatório.</p>
            <div class="report-review-divider"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        _render_item("Zona do lote", _pick_zone(calc))
        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
        _render_item("Rua/Via", _pick_street(calc))
    with c2:
        _render_item(
            "Dimensões do terreno",
            f"{_fmt_num(session_snapshot.get('lot_front_m'))} m × {_fmt_num(session_snapshot.get('lot_depth_m'))} m",
        )
        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
        _render_item("Área do lote", f"{_fmt_num(session_snapshot.get('lot_area_m2'))} m²")

    area_pretendida = calc.get("built_ground_input_m2")
    if area_pretendida not in (None, "", 0, 0.0):
        st.markdown(
            f"""
            <div class="review-highlight">
                <span class="review-item-label">Área pretendida informada</span>
                <span class="review-item-value">{_fmt_num(area_pretendida)} m²</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
