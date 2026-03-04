import streamlit as st
from typing import Any, Dict


def _num(v: Any) -> float | None:
    if v is None:
        return None
    # Decimal (supabase) / int / float / str
    try:
        return float(v)
    except Exception:
        try:
            s = str(v).strip().replace(".", "").replace(",", ".")
            return float(s)
        except Exception:
            return None


def _pct_from_rule(rule: Dict[str, Any], frac_key: str, pct_key: str) -> float | None:
    # prefere *_pct (0-100)
    v_pct = _num(rule.get(pct_key))
    if v_pct is not None:
        return v_pct
    v_frac = _num(rule.get(frac_key))
    if v_frac is None:
        return None
    # to_max/tp_min no schema podem ser 0..1
    if 0 <= v_frac <= 1.0:
        return v_frac * 100.0
    # se já vier em 0..100 por algum motivo, respeita
    return v_frac


def _fmt(v: Any, suffix: str = "") -> str:
    if v is None:
        return "—"
    if isinstance(v, (int, float)):
        return f"{v:.2f}{suffix}" if suffix else f"{v:.2f}"
    return f"{v}{suffix}"


def render_relatorio_section(calc: Dict[str, Any]) -> None:
    st.subheader("6) Relatório Urbanístico")

    if not isinstance(calc, dict) or not calc:
        st.info("Preencha os dados e clique em **Calcular viabilidade** para gerar o relatório.")
        return

    # --- Identificação ---
    zone_sigla = calc.get("zone_sigla") or calc.get("zone")
    street_name = calc.get("street_name") or calc.get("via_nome")
    street_type = calc.get("street_type") or calc.get("via_tipo")
    street_dist = calc.get("street_dist") or calc.get("via_dist_m")
    use_type_code = calc.get("use_type_code")

    st.markdown("### Identificação")
    c1, c2, c3 = st.columns(3)
    c1.write(f"**Zona:** {zone_sigla or '—'}")
    c2.write(f"**Via:** {street_name or '—'}")
    c3.write(f"**Uso:** {use_type_code or '—'}")

    if street_type or street_dist is not None:
        st.caption(
            f"Tipo de via: {street_type or '—'} | Distância: {street_dist if street_dist is not None else '—'} m"
        )

    # --- Regra Supabase (quadro técnico) ---
    st.markdown("### Índices e parâmetros (regra Supabase)")
    rule = calc.get("rule") or {}
    if not isinstance(rule, dict) or not rule:
        st.info("Nenhuma regra carregada (verifique Supabase / zona / uso).")
    else:
        to_max_pct = _pct_from_rule(rule, "to_max", "to_max_pct")
        tp_min_pct = _pct_from_rule(rule, "tp_min", "tp_min_pct")
        to_sub_pct = _pct_from_rule(rule, "to_subsolo_max", "to_subsolo_max_pct")  # raramente existe *_pct
        if to_sub_pct is None:
            to_sub_pct = _pct_from_rule(rule, "to_sub_max", "to_sub_max_pct")

        ia_max = _num(rule.get("ia_max"))
        ia_min = _num(rule.get("ia_min"))

        rec_fr = _num(rule.get("recuo_frontal_m"))
        rec_lat = _num(rule.get("recuo_lateral_m"))
        rec_fun = _num(rule.get("recuo_fundos_m"))

        area_min = _num(rule.get("area_min_lote_m2"))
        area_max = _num(rule.get("area_max_lote_m2"))

        test_min_meio = _num(rule.get("testada_min_meio_m"))
        test_min_esq = _num(rule.get("testada_min_esquina_m"))
        test_max = _num(rule.get("testada_max_m"))

        gab_m = _num(rule.get("gabarito_m"))
        gab_pav = rule.get("gabarito_pav")

        # lote esquina (apenas informativo por enquanto)
        is_corner = bool(calc.get("lote_esquina") or st.session_state.get("lote_esquina", False))
        st.write(f"**Situação do lote:** {'Esquina' if is_corner else 'Meio de quadra'}")

        # Mostra os campos solicitados (sempre)
        r1, r2, r3 = st.columns(3)
        r1.metric("TP mínima", _fmt(tp_min_pct, "%"))
        r2.metric("TO máxima", _fmt(to_max_pct, "%"))
        r3.metric("TO subsolo máx", _fmt(to_sub_pct, "%"))

        r4, r5, r6 = st.columns(3)
        r4.metric("IA máximo", _fmt(ia_max))
        r5.metric("IA mínimo", _fmt(ia_min))
        r6.metric("Altura máx (gabarito)", (f"{_fmt(gab_m, ' m')} | {gab_pav} pav." if gab_pav is not None else _fmt(gab_m, ' m')))

        r7, r8, r9 = st.columns(3)
        r7.metric("Recuo de Frente", _fmt(rec_fr, " m"))
        r8.metric("Recuo Lateral", _fmt(rec_lat, " m"))
        r9.metric("Recuo de Fundo", _fmt(rec_fun, " m"))

        r10, r11, r12 = st.columns(3)
        r10.metric("Área mín do lote", _fmt(area_min, " m²"))
        r11.metric("Área máx do lote", _fmt(area_max, " m²"))
        r12.metric("Testada máx", _fmt(test_max, " m"))

        # Testadas mínimas (mostrar as duas por enquanto)
        st.markdown("**Testada mínima:**")
        ctm1, ctm2 = st.columns(2)
        ctm1.write(f"- Meio de quadra: **{_fmt(test_min_meio, ' m')}**")
        ctm2.write(f"- Esquina: **{_fmt(test_min_esq, ' m')}**")

        with st.expander("Ver regra completa (JSON)"):
            st.json(rule)

    # --- Cálculos ---
    st.markdown("### Cálculos")
    basic = calc.get("basic") or {}
    if isinstance(basic, dict) and basic:
        st.json(basic)
    else:
        st.info("Cálculos ainda não disponíveis (clique em **Calcular viabilidade**).")
