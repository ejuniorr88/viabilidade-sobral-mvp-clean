from __future__ import annotations

from typing import Any, Dict, Optional
import streamlit as st


def _as_float(x: Any) -> Optional[float]:
    if x is None or x == "":
        return None
    try:
        return float(x)
    except Exception:
        return None


def _pick(rule: Dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in rule and rule.get(k) is not None:
            return rule.get(k)
    return None


def _fmt_m2(x: float) -> str:
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m²"


def _fmt_m(x: float) -> str:
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m"


def render_relatorio_section(**kwargs: Any) -> None:
    """
    Seção 6) Relatório Urbanístico (formato pergunta/resposta)

    ✅ Robustez:
    - aceita **kwargs para evitar TypeError quando o app.py mudar.
    - usa testada/profundidade se existirem; senão avisa.
    """
    st.subheader("6) Relatório Urbanístico")

    calc: Dict[str, Any] = kwargs.get("calc") or st.session_state.get("calc", {}) or {}
    rule: Optional[Dict[str, Any]] = calc.get("rule") if isinstance(calc, dict) else None

    lot_area = kwargs.get("lot_area", st.session_state.get("lot_area", 0.0))
    testada = kwargs.get("testada", st.session_state.get("testada", 0.0))
    profundidade = kwargs.get("profundidade", st.session_state.get("profundidade", 0.0))
    built_ground = kwargs.get("built_ground", st.session_state.get("built_ground", 0.0))

    lot_area_f = float(lot_area or 0.0)
    testada_f = float(testada or 0.0)
    profundidade_f = float(profundidade or 0.0)
    built_ground_f = float(built_ground or 0.0)

    if not calc or not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar o relatório.")
        return
    if not rule:
        st.info("Sem regra do Supabase — não é possível montar o relatório completo.")
        return

    zona = calc.get("zone") or "—"
    use_type = calc.get("use_type_code") or "—"
    street_info = calc.get("street_info") or {}
    via_tipo = (street_info.get("via_type") or street_info.get("tipo") or street_info.get("classificacao") or "via local")

    to_max_pct = _as_float(_pick(rule, "to_max_pct", "to_max")) or 0.0
    tp_min_pct = _as_float(_pick(rule, "tp_min_pct", "tp_min")) or 0.0
    ia_max = _as_float(_pick(rule, "ia_max", "ia_maximo")) or 0.0

    rec_frontal = _as_float(_pick(rule, "recuo_frontal_m", "recuo_frontal", "front_setback_m")) or 0.0
    rec_lateral = _as_float(_pick(rule, "recuo_lateral_m", "recuo_lateral", "side_setback_m")) or 0.0
    rec_fundo = _as_float(_pick(rule, "recuo_fundo_m", "recuo_fundo", "rear_setback_m")) or 0.0

    max_to_m2 = lot_area_f * (to_max_pct / 100.0) if lot_area_f else 0.0
    tp_min_m2 = lot_area_f * (tp_min_pct / 100.0) if lot_area_f else 0.0
    ia_total_m2 = lot_area_f * ia_max if lot_area_f else 0.0

    # se não informar área pretendida, assume máximo TO
    if built_ground_f <= 0 and max_to_m2 > 0:
        built_ground_f = max_to_m2

    st.markdown("🏡 **RELATÓRIO URBANÍSTICO**")
    st.markdown(f"**{use_type}**")
    st.write("")
    st.markdown(f"**Terreno:** {_fmt_m2(lot_area_f)}")
    st.markdown(f"**Dimensões:** {_fmt_m(testada_f)} × {_fmt_m(profundidade_f)}")
    st.markdown(f"**Zona:** {zona}")
    st.markdown(f"**Tipo:** {via_tipo}")

    st.write("")
    st.markdown("📍 **1️⃣ Quanto posso ocupar no chão?**")
    st.markdown(f"A zona permite ocupar até **{to_max_pct:.0f}%** do terreno no térreo.")
    st.markdown(f"👉 {_fmt_m2(lot_area_f)} × {to_max_pct:.0f}% = **{_fmt_m2(max_to_m2)}**")
    st.markdown("Esse é o limite máximo permitido pela **Taxa de Ocupação (TO)**.")
    st.write("")
    st.markdown("Agora veja duas situações possíveis:")

    st.write("")
    st.markdown("✅ **Opção 1 – Respeitando os recuos padrão**")
    st.markdown("Recuos exigidos:")
    st.markdown(f"- Frontal: **{_fmt_m(rec_frontal)}**")
    st.markdown(f"- Laterais: **{_fmt_m(rec_lateral)}** cada")
    st.markdown(f"- Fundo: **{_fmt_m(rec_fundo)}**")

    if testada_f > 0 and profundidade_f > 0:
        largura_util = max(testada_f - 2 * rec_lateral, 0.0)
        prof_util = max(profundidade_f - rec_frontal - rec_fundo, 0.0)
        area_recuos = largura_util * prof_util

        st.write("")
        st.markdown("Área interna disponível:")
        st.markdown(f"- Largura útil: {testada_f:.2f} − {rec_lateral:.2f} − {rec_lateral:.2f} = **{largura_util:.2f} m**")
        st.markdown(f"- Profundidade útil: {profundidade_f:.2f} − {rec_frontal:.2f} − {rec_fundo:.2f} = **{prof_util:.2f} m**")
        st.markdown(f"📐 **{largura_util:.2f} × {prof_util:.2f} = {area_recuos:,.2f} m²**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.markdown(
            f"👉 Nesse caso, mesmo podendo ocupar **{_fmt_m2(max_to_m2)}** pela regra da zona, "
            f"o limite físico pelos recuos é **{_fmt_m2(area_recuos)}**."
        )
    else:
        st.warning("⚠️ Para calcular a área interna pelos recuos, informe **Largura (testada)** e **Profundidade** no lote.")

    st.write("")
    st.markdown("✅ **Opção 2 – Implantação no alinhamento (Art. 112 – LC 90/2023)**")
    st.markdown(
        "Por se tratar de **residência unifamiliar**, a legislação pode permitir **zerar recuos frontal e laterais**, desde que:"
    )
    st.markdown("- Seja respeitada a **Taxa de Ocupação (TO)**")
    st.markdown("- Seja respeitada a **Taxa de Permeabilidade (TP)**")
    st.write("")
    st.markdown(f"Nesse caso, você pode utilizar: 👉 **{_fmt_m2(max_to_m2)}** no térreo")
    st.markdown("⚠ O recuo de fundo pode permanecer obrigatório conforme regra/local.")

    st.write("")
    st.markdown("🌿 **2️⃣ Quanto preciso deixar livre?**")
    st.markdown(f"A zona exige **{tp_min_pct:.0f}%** de área permeável.")
    st.markdown(f"👉 {_fmt_m2(lot_area_f)} × {tp_min_pct:.0f}% = **{_fmt_m2(tp_min_m2)}** obrigatórios permeáveis")
    st.write("")
    st.markdown(f"Se você utilizar **{_fmt_m2(max_to_m2)}** no térreo:")
    area_restante = max(lot_area_f - max_to_m2, 0.0)
    st.markdown(f"Área restante no lote: {_fmt_m2(lot_area_f)} − {_fmt_m2(max_to_m2)} = **{_fmt_m2(area_restante)}**")

    st.write("")
    st.markdown("🏢 **3️⃣ Posso construir mais andares?**")
    st.markdown("Além do limite no chão, existe o limite total permitido.")
    st.markdown(f"**Índice de Aproveitamento (IA): {ia_max:.2f}**")
    st.markdown(f"👉 {_fmt_m2(lot_area_f)} × {ia_max:.2f} = **{_fmt_m2(ia_total_m2)}** no total")
