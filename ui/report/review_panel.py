from __future__ import annotations

from typing import Any, Dict

import streamlit as st


_CARD_CSS = """
<style>
.report-review-shell {
    margin: 0.55rem 0 1.05rem 0;
}
.report-review-hero {
    position: relative;
    background: linear-gradient(135deg, #fff7f3 0%, #ffeae4 52%, #fff3ef 100%);
    border: 1px solid #f3c7ba;
    border-left: 7px solid #e15b3d;
    border-radius: 20px;
    padding: 1.15rem 1.2rem 1.1rem 1.2rem;
    box-shadow: 0 12px 28px rgba(225, 91, 61, 0.10);
    overflow: hidden;
}
.report-review-hero::before {
    content: "";
    position: absolute;
    top: -42px;
    right: -32px;
    width: 170px;
    height: 170px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(255,255,255,0.60) 0%, rgba(255,255,255,0.15) 58%, transparent 72%);
    pointer-events: none;
}
.report-review-hero::after {
    content: "";
    position: absolute;
    bottom: -52px;
    left: 42%;
    width: 210px;
    height: 210px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(251,146,60,0.10) 0%, rgba(251,146,60,0.04) 45%, transparent 72%);
    pointer-events: none;
}
.report-review-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    background: rgba(255,255,255,0.92);
    color: #c2410c;
    border: 1px solid rgba(225,91,61,0.20);
    border-radius: 999px;
    padding: 0.34rem 0.78rem;
    font-size: 0.81rem;
    font-weight: 800;
    letter-spacing: 0.01em;
    margin-bottom: 0.72rem;
}
.report-review-title {
    margin: 0;
    font-size: 1.55rem;
    line-height: 1.18;
    font-weight: 800;
    color: #3b1d17;
}
.report-review-subtitle {
    margin: 0.5rem 0 0 0;
    color: #6b2c22;
    font-size: 1rem;
}
.report-review-note {
    margin-top: 0.9rem;
    background: rgba(255,255,255,0.88);
    border: 1px dashed rgba(225,91,61,0.30);
    border-radius: 13px;
    padding: 0.78rem 0.9rem;
    color: #3b1d17;
    font-size: 0.94rem;
    font-weight: 700;
}
.review-grid-gap {
    height: 0.9rem;
}
.review-item {
    background: linear-gradient(180deg, #ffffff 0%, #fffaf8 100%);
    border: 1px solid #f2d4cb;
    border-radius: 16px;
    padding: 1rem 1rem 0.95rem 1rem;
    min-height: 108px;
    box-shadow: 0 6px 18px rgba(59, 23, 13, 0.04);
}
.review-item-label {
    display: inline-block;
    font-size: 0.79rem;
    font-weight: 800;
    color: #c2410c;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.45rem;
}
.review-item-value {
    display: block;
    font-size: 1.12rem;
    font-weight: 800;
    color: #2c1611;
    line-height: 1.42;
    word-break: break-word;
}
.review-item-hint {
    display: block;
    margin-top: 0.35rem;
    font-size: 0.84rem;
    color: #7c5b53;
}
.review-highlight {
    margin-top: 0.95rem;
    background: linear-gradient(135deg, #fff1ee 0%, #ffe2db 100%);
    border: 1px solid #f5b6a6;
    border-left: 6px solid #dc2626;
    border-radius: 16px;
    padding: 0.95rem 1rem;
    box-shadow: 0 8px 20px rgba(220, 38, 38, 0.10);
}
.review-highlight .review-item-label {
    color: #b91c1c;
    margin-bottom: 0.25rem;
}
.review-highlight .review-item-value {
    color: #7f1d1d;
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


def _first_positive(*values: Any) -> float | None:
    for value in values:
        try:
            if value is None or value == "":
                continue
            num = float(value)
            if num > 0:
                return num
        except Exception:
            continue
    return None


def _pick_built_area(calc: Dict[str, Any], session_snapshot: Dict[str, Any]) -> Any:
    return _first_positive(
        session_snapshot.get("built_ground_m2"),
        session_snapshot.get("built_ground_input_m2"),
        calc.get("built_ground_m2"),
        calc.get("built_ground_input_m2"),
        calc.get("built_ground_adopted_m2"),
        st.session_state.get("built_ground_m2"),
        st.session_state.get("built_ground_input_m2"),
        st.session_state.get("built_ground_m2_input"),
    )


def _render_item(label: str, value: str, hint: str | None = None) -> None:
    hint_html = f"<span class='review-item-hint'>{hint}</span>" if hint else ""
    st.markdown(
        f"""
        <div class="review-item">
            <span class="review-item-label">{label}</span>
            <span class="review-item-value">{value}</span>
            {hint_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_review_panel(*, calc: Dict[str, Any], session_snapshot: Dict[str, Any]) -> None:
    st.markdown(_CARD_CSS, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="report-review-shell">
            <div class="report-review-hero">
                <div class="report-review-badge">📋 Revisão obrigatória antes da emissão</div>
                <h3 class="report-review-title">Confirme os dados do relatório</h3>
                <p class="report-review-subtitle">Confira atentamente as informações abaixo antes de seguir. Essa etapa evita gerar o relatório com dados incorretos.</p>
                <div class="report-review-note">Atenção: o relatório será emitido com base exatamente nos dados resumidos nesta conferência.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        _render_item("Zona do lote", _pick_zone(calc), "Verifique se a zona identificada corresponde ao terreno selecionado.")
        st.markdown("<div class='review-grid-gap'></div>", unsafe_allow_html=True)
        _render_item("Rua/Via", _pick_street(calc), "Confirme se a via do lote está correta.")
    with c2:
        _render_item(
            "Dimensões do terreno",
            f"{_fmt_num(session_snapshot.get('lot_front_m'))} m × {_fmt_num(session_snapshot.get('lot_depth_m'))} m",
            "Confira frente e profundidade informadas.",
        )
        st.markdown("<div class='review-grid-gap'></div>", unsafe_allow_html=True)
        _render_item("Área do lote", f"{_fmt_num(session_snapshot.get('lot_area_m2'))} m²", "Área calculada a partir dos dados atuais do lote.")

    area_pretendida = _pick_built_area(calc, session_snapshot)
    if area_pretendida is not None:
        st.markdown(
            f"""
            <div class="review-highlight">
                <span class="review-item-label">Área construída pretendida</span>
                <span class="review-item-value">{_fmt_num(area_pretendida)} m²</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
