from __future__ import annotations

from typing import Any, Dict

import streamlit as st


_CARD_CSS = """
<style>
.report-review-shell {
    margin: 0.45rem 0 1rem 0;
}
.report-review-hero {
    position: relative;
    background: linear-gradient(135deg, #eef6ff 0%, #dbeafe 55%, #fde68a 160%);
    border: 1px solid #c9ddfb;
    border-left: 6px solid #2563eb;
    border-radius: 18px;
    padding: 1.1rem 1.2rem 1.05rem 1.2rem;
    box-shadow: 0 10px 24px rgba(37, 99, 235, 0.08);
    overflow: hidden;
}
.report-review-hero::after {
    content: "";
    position: absolute;
    inset: auto -40px -40px auto;
    width: 140px;
    height: 140px;
    border-radius: 999px;
    background: rgba(255,255,255,0.25);
    pointer-events: none;
}
.report-review-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    background: rgba(255,255,255,0.86);
    color: #1d4ed8;
    border: 1px solid rgba(37,99,235,0.18);
    border-radius: 999px;
    padding: 0.3rem 0.7rem;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.01em;
    margin-bottom: 0.65rem;
}
.report-review-title {
    margin: 0;
    font-size: 1.45rem;
    line-height: 1.2;
    font-weight: 800;
    color: #0f172a;
}
.report-review-subtitle {
    margin: 0.45rem 0 0 0;
    color: #334155;
    font-size: 0.98rem;
}
.report-review-note {
    margin-top: 0.85rem;
    background: rgba(255,255,255,0.78);
    border: 1px dashed rgba(37,99,235,0.26);
    border-radius: 12px;
    padding: 0.7rem 0.85rem;
    color: #1e293b;
    font-size: 0.93rem;
    font-weight: 600;
}
.review-grid-gap {
    height: 0.85rem;
}
.review-item {
    background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
    border: 1px solid #d7e6fb;
    border-radius: 16px;
    padding: 1rem 1rem 0.95rem 1rem;
    min-height: 108px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04);
}
.review-item-label {
    display: inline-block;
    font-size: 0.79rem;
    font-weight: 800;
    color: #1d4ed8;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.45rem;
}
.review-item-value {
    display: block;
    font-size: 1.12rem;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.42;
    word-break: break-word;
}
.review-item-hint {
    display: block;
    margin-top: 0.35rem;
    font-size: 0.84rem;
    color: #64748b;
}
.review-highlight {
    margin-top: 0.95rem;
    background: linear-gradient(135deg, #fff7ed 0%, #fffbeb 100%);
    border: 1px solid #fed7aa;
    border-left: 6px solid #f59e0b;
    border-radius: 16px;
    padding: 0.95rem 1rem;
    box-shadow: 0 8px 20px rgba(245, 158, 11, 0.08);
}
.review-highlight .review-item-label {
    color: #b45309;
    margin-bottom: 0.25rem;
}
.review-highlight .review-item-value {
    color: #7c2d12;
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
