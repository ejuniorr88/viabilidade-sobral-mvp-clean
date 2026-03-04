import streamlit as st
from typing import Any, Dict


def _fmt_num(v: Any, *, suffix: str = "", decimals: int = 2) -> str:
    if v is None or v == "":
        return "—"
    try:
        # supabase pode vir Decimal
        x = float(v)
        if suffix == "%":
            return f"{x:.{decimals}f}{suffix}"
        return f"{x:.{decimals}f}{suffix}"
    except Exception:
        return str(v)


def _to_pct(rule: Dict[str, Any], key_pct: str, key_frac: str) -> Any:
    """Retorna percentual (0..100). Usa *_pct se existir, senão converte fração 0..1."""
    if not isinstance(rule, dict):
        return None
    v = rule.get(key_pct)
    if v is not None:
        return v
    v2 = rule.get(key_frac)
    if v2 is None:
        return None
    try:
        return float(v2) * 100.0
    except Exception:
        return None


def render_relatorio_section(calc: Dict[str, Any]) -> None:
    st.subheader("6) Relatório Urbanístico")

    if not isinstance(calc, dict) or not calc:
        st.info("Preencha os dados e clique em **Calcular viabilidade** para gerar o relatório.")
        return

    # Identificação (aceita chaves novas e antigas)
    zone = calc.get("zone") or calc.get("zone_sigla")
    street_name = calc.get("via_nome") or calc.get("street_name")
    street_type = calc.get("via_tipo") or calc.get("street_type")
    street_dist = calc.get("via_dist_m") or calc.get("street_dist")
    use_type_code = calc.get("use_type_code")

    # Lote
    lot_area = calc.get("lot_area_m2")
    lot_front = calc.get("lot_front_m")
    lot_depth = calc.get("lot_depth_m")
    is_corner = bool(calc.get("lot_is_corner", False))

    st.markdown("### Identificação")
    c1, c2, c3, c4 = st.columns(4)
    c1.write(f"**Zona:** {zone or '—'}")
    c2.write(f"**Via:** {street_name or '—'}")
    c3.write(f"**Uso:** {use_type_code or '—'}")
    c4.write(f"**Lote:** {'Esquina' if is_corner else 'Meio de quadra'}")

    if street_type or street_dist is not None:
        st.caption(f"Tipo de via: {street_type or '—'} | Distância: {street_dist if street_dist is not None else '—'} m")

    st.markdown("### Quadro técnico – Parâmetros urbanísticos (zone_rules)")

    rule = calc.get("rule") or {}
    if not isinstance(rule, dict) or not rule:
        st.info("Regra ainda não carregada (Supabase).")
        return

    # Normalização TO/TP
    to_max_pct = _to_pct(rule, "to_max_pct", "to_max")
    tp_min_pct = _to_pct(rule, "tp_min_pct", "tp_min")

    # Campos diretos
    ia_max = rule.get("ia_max")
    ia_min = rule.get("ia_min")
    rec_f = rule.get("recuo_frontal_m")
    rec_l = rule.get("recuo_lateral_m")
    rec_fd = rule.get("recuo_fundos_m")
    g_m = rule.get("gabarito_m")
    g_pav = rule.get("gabarito_pav")

    area_min = rule.get("area_min_lote_m2")
    area_max = rule.get("area_max_lote_m2")
    test_min_meio = rule.get("testada_min_meio_m")
    test_min_esq = rule.get("testada_min_esquina_m")
    test_max = rule.get("testada_max_m")

    to_sub = rule.get("to_sub_max")
    if to_sub is None:
        to_sub = rule.get("to_subsolo_max")

    # Exibição em 2 colunas (sem depender de pandas)
    left, right = st.columns(2)

    with left:
        st.write(f"**Zona:** {zone or '—'}")
        st.write(f"**TP mínima:** {_fmt_num(tp_min_pct, suffix='%')}")
        st.write(f"**TO máxima:** {_fmt_num(to_max_pct, suffix='%')}")
        st.write(f"**TO do Subsolo máxima:** {_fmt_num(to_sub, suffix='%')}")
        st.write(f"**IA máximo:** {_fmt_num(ia_max, decimals=3)}")
        st.write(f"**IA mínimo:** {_fmt_num(ia_min, decimals=3)}")

        st.write(f"**Recuo de Frente:** {_fmt_num(rec_f, suffix=' m')}")
        st.write(f"**Recuo Lateral:** {_fmt_num(rec_l, suffix=' m')}")
        st.write(f"**Recuo de Fundo:** {_fmt_num(rec_fd, suffix=' m')}")

    with right:
        st.write(f"**Área mínima do lote:** {_fmt_num(area_min, suffix=' m²')}")
        st.write(f"**Área máxima do lote:** {_fmt_num(area_max, suffix=' m²')}")
        st.write(f"**Testada mínima (meio):** {_fmt_num(test_min_meio, suffix=' m')}")
        st.write(f"**Testada mínima (esquina):** {_fmt_num(test_min_esq, suffix=' m')}")
        st.write(f"**Testada máxima:** {_fmt_num(test_max, suffix=' m')}")

        # Gabarito
        if g_m is None and g_pav is None:
            st.write("**Altura máxima (gabarito):** —")
        else:
            if g_pav is not None:
                st.write(f"**Altura máxima (gabarito):** {_fmt_num(g_m, suffix=' m')} (≈ {g_pav} pav.)")
            else:
                st.write(f"**Altura máxima (gabarito):** {_fmt_num(g_m, suffix=' m')}")

    st.divider()

    st.markdown("### Dados do lote (informados)")
    st.write(f"**Área do lote:** {_fmt_num(lot_area, suffix=' m²')}")
    st.write(f"**Dimensões:** {_fmt_num(lot_front, suffix=' m')} × {_fmt_num(lot_depth, suffix=' m')}")
    st.write(f"**Situação:** {'Esquina' if is_corner else 'Meio de quadra'}")

    with st.expander("Ver dados brutos (calc/rule)"):
        st.json({"calc": calc, "rule": rule})
