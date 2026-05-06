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
    background: linear-gradient(135deg, #fff8f5 0%, #ffefe9 52%, #fff7f4 100%);
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
.report-review-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    background: rgba(255,255,255,0.92);
    color: #111827;
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
    color: #2c1611;
}
.report-review-subtitle {
    margin: 0.5rem 0 0 0;
    color: #5b3a33;
    font-size: 1rem;
}
.report-review-note {
    margin-top: 0.9rem;
    background: rgba(255,255,255,0.90);
    border: 1px dashed rgba(225,91,61,0.30);
    border-radius: 13px;
    padding: 0.78rem 0.9rem;
    color: #2c1611;
    font-size: 0.94rem;
    font-weight: 700;
}
.report-type-card {
    margin: 0.9rem 0 1rem 0;
    background: linear-gradient(180deg, #ffffff 0%, #fffaf8 100%);
    border: 1px solid #f2d4cb;
    border-left: 6px solid #173b69;
    border-radius: 18px;
    padding: 1rem 1.05rem 0.95rem 1.05rem;
    box-shadow: 0 8px 20px rgba(23, 59, 105, 0.06);
}
.report-type-eyebrow {
    display: inline-block;
    font-size: 0.76rem;
    font-weight: 900;
    color: #173b69;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.45rem;
}
.report-type-title {
    margin: 0;
    font-size: 1.12rem;
    line-height: 1.32;
    font-weight: 900;
    color: #111827;
}
.report-type-description {
    margin: 0.42rem 0 0 0;
    font-size: 0.96rem;
    line-height: 1.48;
    color: #374151;
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
    color: #111827;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.45rem;
}
.review-item-value {
    display: block;
    font-size: 1.12rem;
    font-weight: 800;
    color: #111827;
    line-height: 1.42;
    word-break: break-word;
}
.review-item-hint {
    display: block;
    margin-top: 0.35rem;
    font-size: 0.84rem;
    color: #6b7280;
}
.review-item-hint.area-zero-hint {
    font-size: 1rem;
    line-height: 1.5;
    color: #374151;
}
.review-item-hint.area-zero-hint strong {
    font-weight: 800;
    color: #111827;
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


_PROJECT_TYPE_INFO: Dict[str, Dict[str, str]] = {
    "RES_UNI": {
        "title": "Residência Unifamiliar",
        "description": "É a edificação residencial destinada a uma única unidade habitacional, ou seja, uma casa para uma família no lote.",
    },
    "RES_MULTI_R21": {
        "title": "R2.1",
        "description": "É a residência multifamiliar horizontal com 2 unidades no mesmo lote, que podem ser lado a lado ou uma sobre a outra, cada uma com acesso independente para a via pública.",
    },
    "RES_MULTI_R22": {
        "title": "R2.2",
        "description": "É a residência multifamiliar horizontal em forma de condomínio horizontal, com várias unidades e acesso por circulação interna, sem que cada unidade tenha saída direta para a rua.",
    },
    "RES_MULTI_R3": {
        "title": "R3",
        "description": "É a residência multifamiliar vertical, implantada em forma de edifício, ou seja, um prédio com várias moradias no mesmo bloco.",
    },
}


def _normalize_use_type_code(value: Any) -> str:
    return str(value or "").strip().upper()


def _pick_use_type_code(calc: Dict[str, Any], session_snapshot: Dict[str, Any]) -> str:
    candidates = [
        calc.get("use_type_code"),
        calc.get("requested_use_type_code"),
        calc.get("resolved_use_type_code"),
        session_snapshot.get("use_type_code"),
        st.session_state.get("selected_use_code"),
        st.session_state.get("use_type_code"),
        (st.session_state.get("calc") or {}).get("use_type_code") if isinstance(st.session_state.get("calc"), dict) else None,
    ]
    for candidate in candidates:
        code = _normalize_use_type_code(candidate)
        if code:
            return code
    return "RES_UNI"


def _get_project_type_info(use_type_code: Any) -> Dict[str, str]:
    code = _normalize_use_type_code(use_type_code)
    if code in _PROJECT_TYPE_INFO:
        return _PROJECT_TYPE_INFO[code]
    if code.startswith("RES_MULTI"):
        return {
            "title": "Residência Multifamiliar",
            "description": "É uma tipologia residencial com mais de uma unidade habitacional no mesmo lote ou empreendimento. Confira se o subtipo selecionado corresponde ao projeto pretendido.",
        }
    return _PROJECT_TYPE_INFO["RES_UNI"]


def _render_project_type_card(*, calc: Dict[str, Any], session_snapshot: Dict[str, Any]) -> None:
    info = _get_project_type_info(_pick_use_type_code(calc, session_snapshot))
    st.markdown(
        f"""
        <div class="report-type-card">
            <span class="report-type-eyebrow">Tipo de projeto selecionado</span>
            <h4 class="report-type-title">{info['title']}</h4>
            <p class="report-type-description">{info['description']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _to_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _pick_built_area(calc: Dict[str, Any], session_snapshot: Dict[str, Any]) -> float | None:
    candidates = [
        session_snapshot.get("built_ground_m2"),
        session_snapshot.get("built_ground_input_m2"),
        session_snapshot.get("built_ground_m2_input"),
        calc.get("built_ground_m2"),
        calc.get("built_ground_input_m2"),
        calc.get("built_ground_adopted_m2"),
        calc.get("built_ground"),
        st.session_state.get("built_ground_m2"),
        st.session_state.get("built_ground_input_m2"),
        st.session_state.get("built_ground_m2_input"),
    ]
    for value in candidates:
        num = _to_float(value)
        if num is not None and num > 0:
            return num
    return None


def _render_item(label: str, value: str, hint: str | None = None, hint_class: str = "") -> None:
    hint_classes = f"review-item-hint {hint_class}".strip()
    hint_html = f"<span class='{hint_classes}'>{hint}</span>" if hint else ""
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

    _render_project_type_card(calc=calc, session_snapshot=session_snapshot)

    is_irregular = bool(
        session_snapshot.get("lot_is_irregular")
        or calc.get("lot_irregular")
        or calc.get("lot_is_irregular")
    )
    dimensoes_value = (
        "Terreno irregular — área total informada"
        if is_irregular
        else f"{_fmt_num(session_snapshot.get('lot_front_m'))} m × {_fmt_num(session_snapshot.get('lot_depth_m'))} m"
    )
    dimensoes_hint = (
        "Testada e profundidade não entram no cálculo deste terreno."
        if is_irregular
        else "Confira frente e profundidade informadas."
    )
    area_hint = (
        "Área total informada para o terreno irregular."
        if is_irregular
        else "Área calculada a partir dos dados atuais do lote."
    )

    c1, c2 = st.columns(2)
    with c1:
        _render_item("Zona do lote", _pick_zone(calc), "Verifique se a zona identificada corresponde ao terreno selecionado.")
        st.markdown("<div class='review-grid-gap'></div>", unsafe_allow_html=True)
        _render_item("Rua/Via", _pick_street(calc), "Confirme se a via do lote está correta.")
    with c2:
        _render_item(
            "Dimensões do terreno",
            dimensoes_value,
            dimensoes_hint,
        )
        st.markdown("<div class='review-grid-gap'></div>", unsafe_allow_html=True)
        _render_item("Área do lote", f"{_fmt_num(session_snapshot.get('lot_area_m2'))} m²", area_hint)

    area_pretendida = _pick_built_area(calc, session_snapshot)
    if area_pretendida is None:
        area_value = "Não informada"
        area_hint = (
            "<strong>"
            "Caso você ainda esteja fazendo um estudo em fase inicial e não saiba a área construída no térreo, "
            "pode deixar o campo como 0. Assim, o sistema calcula o potencial máximo permitido para o lote "
            "selecionado, ajudando você a compreender a capacidade construtiva conforme os parâmetros "
            "urbanísticos aplicáveis."
            "</strong>"
        )
        area_hint_class = "area-zero-hint"
    else:
        area_value = f"{_fmt_num(area_pretendida)} m²"
        area_hint = "Valor informado pelo usuário para a área construída pretendida."
        area_hint_class = ""

    st.markdown("<div class='review-grid-gap'></div>", unsafe_allow_html=True)
    _render_item("Área construída pretendida", area_value, area_hint, area_hint_class)
