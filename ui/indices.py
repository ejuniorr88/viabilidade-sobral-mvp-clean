from __future__ import annotations

from typing import Any, Dict, Optional, Callable

import streamlit as st


def _to_float(v: Any) -> Optional[float]:
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        s = str(v).strip()
        if not s:
            return None
        # pt-BR safety: "1.234,56" -> "1234.56"
        s = s.replace(".", "").replace(",", ".")
        return float(s)
    except Exception:
        return None


def _pct_from_rule(rule: Dict[str, Any], pct_key: str, frac_key: str) -> Optional[float]:
    """
    Normaliza percentuais:
      - Se existir *_pct, usa direto (ex.: 60)
      - Senão, se existir fração 0..1 (ex.: 0.60), converte para 60
    """
    pct = _to_float(rule.get(pct_key))
    if pct is not None:
        return pct
    frac = _to_float(rule.get(frac_key))
    if frac is None:
        return None
    return frac * 100.0 if 0 <= frac <= 1 else frac


def _fmt(v: Any, *, unit: str = "") -> str:
    if v is None or v == "":
        return "—"
    if isinstance(v, (int, float)):
        fv = float(v)
        if abs(fv - round(fv)) < 1e-9:
            s = str(int(round(fv)))
        else:
            s = f"{fv:.2f}"
        return f"{s}{unit}"
    return f"{v}{unit}"


def _render_indices_core(calc: Dict[str, Any]) -> None:
    st.header("4) Índices Urbanísticos (Supabase)")

    zone = calc.get("zone") or calc.get("zone_sigla")
    use_type = calc.get("use_type_code")
    rule = calc.get("rule")

    if not zone or not use_type:
        st.info("Clique em Calcular viabilidade para carregar zona, via e regras do Supabase.")
        return

    if not rule:
        st.info("Clique em Calcular viabilidade para carregar zona, via e regras do Supabase.")
        return

    # Percentuais normalizados
    tp_min_pct = _pct_from_rule(rule, "tp_min_pct", "tp_min")
    to_max_pct = _pct_from_rule(rule, "to_max_pct", "to_max")

    # TO subsolo: dois campos possíveis (podem vir como fração ou %)
    to_sub_pct: Optional[float] = None
    if rule.get("to_sub_max") is not None:
        to_sub_pct = _pct_from_rule(rule, "to_sub_max", "to_sub_max")
    elif rule.get("to_subsolo_max") is not None:
        to_sub_pct = _pct_from_rule(rule, "to_subsolo_max", "to_subsolo_max")

    ia_max = _to_float(rule.get("ia_max"))
    ia_min = _to_float(rule.get("ia_min"))

    rf = _to_float(rule.get("recuo_frontal_m"))
    rl = _to_float(rule.get("recuo_lateral_m"))
    rfd = _to_float(rule.get("recuo_fundos_m"))

    area_min = _to_float(rule.get("area_min_lote_m2"))
    area_max = _to_float(rule.get("area_max_lote_m2"))

    test_min_meio = _to_float(rule.get("testada_min_meio_m"))
    test_min_esq = _to_float(rule.get("testada_min_esquina_m"))
    test_max = _to_float(rule.get("testada_max_m"))

    gabarito_m = _to_float(rule.get("gabarito_m"))
    gabarito_pav = rule.get("gabarito_pav")

    # ===== Cards (mantém estilo existente) =====
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Zona", zone or "—")
    with c2:
        st.metric("Taxa de Permeabilidade (TP) mínima", _fmt(tp_min_pct, unit="%") if tp_min_pct is not None else "—")
    with c3:
        st.metric("Taxa de Ocupação (TO) máxima", _fmt(to_max_pct, unit="%") if to_max_pct is not None else "—")

    c4, c5, c6 = st.columns(3)
    with c4:
        st.metric("TO do Subsolo máxima", _fmt(to_sub_pct, unit="%") if to_sub_pct is not None else "—")
    with c5:
        st.metric("Índice de Aproveitamento (IA) máximo", _fmt(ia_max) if ia_max is not None else "—")
    with c6:
        st.metric("Índice de Aproveitamento (IA) mínimo", _fmt(ia_min) if ia_min is not None else "—")

    c7, c8, c9 = st.columns(3)
    with c7:
        st.metric("Recuo de Frente", _fmt(rf, unit=" m") if rf is not None else "—")
    with c8:
        st.metric("Recuo de Fundo", _fmt(rfd, unit=" m") if rfd is not None else "—")
    with c9:
        st.metric("Recuo Lateral", _fmt(rl, unit=" m") if rl is not None else "—")

    c10, c11, c12 = st.columns(3)
    with c10:
        st.metric("Área mínima do lote", _fmt(area_min, unit=" m²") if area_min is not None else "—")
    with c11:
        # "Testada mínima" com detalhe (meio + esquina)
        if test_min_meio is None and test_min_esq is None:
            st.metric("Testada mínima", "—")
        else:
            primary = test_min_meio if test_min_meio is not None else test_min_esq
            st.metric("Testada mínima", _fmt(primary, unit=" m") if primary is not None else "—")
            st.caption(
                f"Meio de quadra: {(_fmt(test_min_meio, unit=' m') if test_min_meio is not None else '—')}  |  "
                f"Esquina: {(_fmt(test_min_esq, unit=' m') if test_min_esq is not None else '—')}"
            )
    with c12:
        if gabarito_m is None:
            st.metric("Altura máxima (gabarito)", "—")
        else:
            extra = f" ({gabarito_pav} pav.)" if isinstance(gabarito_pav, int) and gabarito_pav > 0 else ""
            st.metric("Altura máxima (gabarito)", f"{_fmt(gabarito_m, unit=' m')}{extra}")

    c13, c14, c15 = st.columns(3)
    with c13:
        st.metric("Área máxima do lote", _fmt(area_max, unit=" m²") if area_max is not None else "—")
    with c14:
        st.metric("Testada máxima", _fmt(test_max, unit=" m") if test_max is not None else "—")
    with c15:
        # sem mexer no layout: mostra subzona
        subzone = rule.get("subzone_code")
        requires_subzone = rule.get("requires_subzone")
        if requires_subzone:
            st.metric("Subzona", subzone or "—")
        else:
            st.metric("Subzona", subzone or "PADRAO")

    with st.expander("Ver regra bruta (JSON do Supabase)"):
        st.json(rule)


def render_indices_section(
    *,
    calc: Dict[str, Any],
    card_func: Optional[Callable[..., Any]] = None,
    pick_func: Optional[Callable[[Dict[str, Any], str], Any]] = None,
    get_rule_func: Optional[Callable[..., Any]] = None,
    **_ignored: Any,
) -> None:
    """
    Wrapper compatível com o app.py atual.
    O app chama: render_indices_section(calc=calc, card_func=..., pick_func=..., get_rule_func=...)
    Nós ignoramos card_func/pick_func porque a renderização aqui é direta, mas NÃO quebra.
    """
    _render_indices_core(calc)
