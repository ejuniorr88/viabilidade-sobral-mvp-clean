import streamlit as st

def _pick(d: dict, keys, default=None):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default

def _to_float(x, default=0.0):
    try:
        if x is None:
            return default
        if isinstance(x, (int, float)):
            return float(x)
        s = str(x).strip().replace("%", "").replace(" ", "")
        # pt-BR number support: 1.234,56
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", ".")
        return float(s)
    except Exception:
        return default

def _fmt_m(v: float) -> str:
    return f"{v:.2f}".replace(".", ",")

def _fmt_m2(v: float) -> str:
    return f"{v:.2f}".replace(".", ",")

def render_relatorio_section():
    """Renderiza o Relatório Urbanístico (sem mudar layout do app)."""
    st.subheader("6) Relatório Urbanístico")

    calc = st.session_state.get("calc")
    lote = st.session_state.get("lote")

    if not calc or not lote:
        st.info("Clique em **Calcular viabilidade** para gerar o relatório.")
        return

    rule = calc.get("rule") or {}

    # Identificação
    zona = calc.get("zone_sigla") or calc.get("zona") or "-"
    via_tipo = calc.get("via_type") or calc.get("tipo_via") or "-"
    rua_nome = calc.get("street_name") or calc.get("rua") or "-"

    st.markdown(f"**Zona:** {zona}  \n**Tipo:** {via_tipo}  \n**Rua/Logradouro:** {rua_nome}")

    # Dados do lote
    lot_area = _to_float(lote.get("area_m2"), 0.0)
    testada = _to_float(lote.get("testada_m"), 0.0)
    profundidade = _to_float(lote.get("profundidade_m"), 0.0)
    area_terreo_user = _to_float(lote.get("area_terreo_m2"), 0.0)

    # Índices (tolerante a nomes)
    to_max_pct = _to_float(_pick(rule, ["to_max_pct", "to_max", "taxa_ocupacao_max", "to"], None), 0.0)
    tp_min_pct = _to_float(_pick(rule, ["tp_min_pct", "tp_min", "taxa_permeabilidade_min", "tp"], None), 0.0)

    # Recuos (tolerante a nomes)
    rec_frontal = _to_float(_pick(rule, ["recuo_frontal_m", "recuo_frontal", "front_setback_m"], None), 0.0)
    rec_lateral = _to_float(_pick(rule, ["recuo_lateral_m", "recuo_lateral", "side_setback_m"], None), 0.0)
    rec_fundo = _to_float(_pick(rule, ["recuo_fundo_m", "recuo_fundo", "rear_setback_m"], None), 0.0)

    st.markdown("---")
    st.markdown("#### 📍 1) Quanto posso ocupar no chão?")

    max_to_area = lot_area * (to_max_pct / 100.0) if lot_area and to_max_pct else 0.0
    if area_terreo_user and area_terreo_user > 0:
        area_terreo = area_terreo_user
        st.write(f"Você informou **{_fmt_m2(area_terreo)} m²** de área no térreo.")
        st.caption("Se deixar 0, o sistema assume o máximo permitido pela Taxa de Ocupação (TO).")
    else:
        area_terreo = max_to_area
        st.write(f"Como a área do térreo ficou **0**, o sistema assume o máximo pela TO: **{_fmt_m2(area_terreo)} m²**.")

    if max_to_area:
        st.write(f"A zona permite ocupar até **{to_max_pct:.0f}%** do terreno no térreo.")
        st.write(f"👉 { _fmt_m2(lot_area) } m² × {to_max_pct:.0f}% = **{_fmt_m2(max_to_area)} m²**")
    else:
        st.warning("TO máxima não encontrada na regra (Supabase).")

    st.markdown("---")
    st.markdown("#### 📍 2) Recuos (implantação)")

    st.write("**Recuos exigidos:**")
    st.markdown(
        f"- Frontal: **{_fmt_m(rec_frontal)} m**\n"
        f"- Laterais: **{_fmt_m(rec_lateral)} m** (cada lado)\n"
        f"- Fundo: **{_fmt_m(rec_fundo)} m**"
    )

    largura_util = max(0.0, testada - 2.0 * rec_lateral)
    prof_util = max(0.0, profundidade - rec_frontal - rec_fundo)
    area_implantavel_por_recuo = largura_util * prof_util

    st.write("**Área interna disponível (por recuos):**")
    st.markdown(
        f"- Largura útil: { _fmt_m(testada) } − { _fmt_m(rec_lateral) } − { _fmt_m(rec_lateral) } = **{_fmt_m(largura_util)} m**\n"
        f"- Profundidade útil: { _fmt_m(profundidade) } − { _fmt_m(rec_frontal) } − { _fmt_m(rec_fundo) } = **{_fmt_m(prof_util)} m**\n"
        f"🔺 { _fmt_m(largura_util) } × { _fmt_m(prof_util) } = **{_fmt_m2(area_implantavel_por_recuo)} m²**"
    )

    if max_to_area:
        limite_final = min(max_to_area, area_implantavel_por_recuo) if area_implantavel_por_recuo else max_to_area
        if area_implantavel_por_recuo and area_implantavel_por_recuo < max_to_area:
            st.write(f"👉 Neste caso, **os recuos** limitam a implantação em **{_fmt_m2(area_implantavel_por_recuo)} m²**.")
        else:
            st.write(f"👉 Neste caso, **a TO** limita a implantação em **{_fmt_m2(max_to_area)} m²**.")
        st.write(f"**Limite prático para o térreo:** **{_fmt_m2(limite_final)} m²**")

    st.markdown("---")
    st.markdown("#### 📍 3) Área permeável (estimativa automática)")

    if tp_min_pct and lot_area:
        min_perm = lot_area * (tp_min_pct / 100.0)
        perm_prev = max(0.0, lot_area - area_terreo) if lot_area else 0.0
        st.write(f"A zona exige **{tp_min_pct:.0f}%** de área permeável mínima.")
        st.write(f"👉 Mínimo: { _fmt_m2(lot_area) } m² × {tp_min_pct:.0f}% = **{_fmt_m2(min_perm)} m²**")
        st.write(f"👉 Estimativa do que sobra (terreno − térreo): **{_fmt_m2(perm_prev)} m²**")

        if perm_prev + 1e-9 >= min_perm:
            st.success("✅ Pela estimativa automática, atende ao mínimo de permeabilidade.")
        else:
            st.error("❌ Pela estimativa automática, **não** atende ao mínimo de permeabilidade.")
            st.caption("Obs.: a área permeável real depende do projeto (pavimentos impermeáveis, pisos drenantes, etc.).")
    else:
        st.warning("TP mínima não encontrada na regra (Supabase).")

__all__ = ["render_relatorio_section"]
