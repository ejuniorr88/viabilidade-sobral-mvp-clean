from __future__ import annotations

from typing import Any, Dict, Optional

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
        # pt-BR safety
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
    # se vier como fração (0..1), converte; se vier já em %, mantém
    return frac * 100.0 if 0 <= frac <= 1 else frac


def _fmt(v: Any, *, unit: str = "") -> str:
    if v is None or v == "":
        return "—"
    if isinstance(v, (int, float)):
        # manter formatação simples, sem mexer em cores/estilos
        s = f"{v:.1f}" if abs(float(v)) >= 10 and float(v).is_integer() is False else f"{v:.2f}"
        # limpar .00 quando for inteiro
        try:
            fv = float(v)
            if abs(fv - round(fv)) < 1e-9:
                s = f"{int(round(fv))}"
        except Exception:
            pass
        return f"{s}{unit}"
    return f"{v}{unit}"


def render_indices_section(*, calc: Dict[str, Any]) -> None:
    """
    Item 4 - NÃO muda layout/ordem geral do app.
    Apenas completa parâmetros que já existem no schema.
    """
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

    # Normalizações
    tp_min_pct = _pct_from_rule(rule, "tp_min_pct", "tp_min")
    to_max_pct = _pct_from_rule(rule, "to_max_pct", "to_max")

    # TO subsolo: pode ter dois campos no schema
    to_sub_pct = None
    # alguns bancos podem armazenar como fração 0..1 também
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
    # gabarito_pav é opcional (não é “parâmetro do item 4” obrigatório, mas útil)
    gabarito_pav = rule.get("gabarito_pav")

    # ============ CARDS ============
    # Mantém grid de 3 colunas como está, só completa com novos cards.
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
        # manter o label "Testada mínima", mas agora mostrar as duas
        if test_min_meio is None and test_min_esq is None:
            st.metric("Testada mínima", "—")
        else:
            # métrica não suporta múltiplas linhas, então colocamos a principal e detalhamos abaixo
            primary = _fmt(test_min_meio, unit=" m") if test_min_meio is not None else (_fmt(test_min_esq, unit=" m") if test_min_esq is not None else "—")
            st.metric("Testada mínima", primary)
            st.caption(
                f"Meio de quadra: {(_fmt(test_min_meio, unit=' m') if test_min_meio is not None else '—')}  |  "
                f"Esquina: {(_fmt(test_min_esq, unit=' m') if test_min_esq is not None else '—')}"
            )
    with c12:
        # gabarito
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
        # espaço reservado para não alterar muito o layout; mostra subzona se relevante
        subzone = rule.get("subzone_code")
        requires_subzone = rule.get("requires_subzone")
        if requires_subzone:
            st.metric("Subzona", subzone or "—")
        else:
            st.metric("Subzona", subzone or "PADRAO")

    with st.expander("Ver regra bruta (JSON do Supabase)"):
        st.json(rule)
