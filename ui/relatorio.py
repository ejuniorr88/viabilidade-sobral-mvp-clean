from __future__ import annotations

from typing import Any, Dict, Optional, Callable

import streamlit as st


def _fmt_m2(v: float) -> str:
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m²"


def _fmt_m(v: float) -> str:
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m"


def render_relatorio_section(
    *,
    calc: Dict[str, Any],
    lot_area: float,
    testada: float,
    profundidade: float,
    built_ground: float,
    pick_func: Callable[..., Any],
    as_float_func: Callable[[Any], Optional[float]],
) -> None:
    st.subheader("6) Relatório Urbanístico")

    if not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar o relatório.")
        return

    rule = calc.get("rule") or {}
    zone = calc.get("zone") or "—"
    street_info = calc.get("street_info") or {}
    via_tipo = street_info.get("tipo") or street_info.get("name") or "—"
    use_type_code = calc.get("use_type_code") or "RES_UNI"

    # índices
    to_max = as_float_func(pick_func(rule, "to_max_pct", "to_max"))
    tp_min = as_float_func(pick_func(rule, "tp_min_pct", "tp_min"))
    ia_max = as_float_func(pick_func(rule, "ia_max", "ia_maximo"))

    rec_front = as_float_func(pick_func(rule, "recuo_frente_m", "recuo_frontal_m", "recuo_frente"))
    rec_lat = as_float_func(pick_func(rule, "recuo_lateral_m", "recuo_lateral"))
    rec_back = as_float_func(pick_func(rule, "recuo_fundo_m", "recuo_fundo"))

    # fallback recuos comuns se vierem vazios
    rec_front = rec_front if rec_front is not None else 3.0
    rec_lat = rec_lat if rec_lat is not None else 1.5
    rec_back = rec_back if rec_back is not None else 1.5

    # 1) área máxima no térreo pela TO
    to_max_pct = (to_max / 100.0) if (to_max is not None and to_max > 1.0) else (to_max if to_max is not None else None)
    # casos: Supabase pode vir 60 (percent) ou 0.6 (fração). Tentamos normalizar.
    if to_max is None:
        to_max_pct = None
    else:
        if to_max > 1.0:
            to_max_pct = to_max / 100.0
        else:
            to_max_pct = to_max

    area_to = lot_area * to_max_pct if to_max_pct is not None else 0.0

    # se usuário não informou área pretendida, assume o máximo permitido (pela TO)
    area_terreo_usada = built_ground if built_ground and built_ground > 0 else area_to

    st.markdown("🏡 **RELATÓRIO URBANÍSTICO**")
    st.markdown(f"**{use_type_code}**")
    st.markdown(f"**Terreno:** {_fmt_m2(lot_area)}")
    st.markdown(f"**Dimensões:** {_fmt_m(testada)} × {_fmt_m(profundidade)}")
    st.markdown(f"**Zona:** {zone}")
    st.markdown(f"**Tipo:** {via_tipo}")

    st.markdown("📍 **1️⃣ Quanto posso ocupar no chão?**")

    if to_max_pct is None:
        st.warning("Sem Taxa de Ocupação (TO) na regra do Supabase.")
        return

    st.markdown(f"A zona permite ocupar até **{to_max_pct*100:.0f}%** do terreno no térreo.")
    st.markdown(f"👉 {_fmt_m2(lot_area)} × **{to_max_pct*100:.0f}%** = **{_fmt_m2(area_to)}**")
    st.markdown("Esse é o limite máximo permitido pela **Taxa de Ocupação (TO)**.")
    st.markdown("Agora veja duas situações possíveis:")

    # Opção 1: com recuos
    st.markdown("✅ **Opção 1 – Respeitando os recuos padrão**")
    st.markdown("Recuos exigidos:")
    st.markdown(f"- Frontal: **{_fmt_m(rec_front)}**")
    st.markdown(f"- Laterais: **{_fmt_m(rec_lat)}** cada")
    st.markdown(f"- Fundo: **{_fmt_m(rec_back)}**")

    largura_util = max(testada - (2 * rec_lat), 0.0)
    profund_util = max(profundidade - rec_front - rec_back, 0.0)
    area_recuos = largura_util * profund_util

    st.markdown("Área interna disponível:")
    st.markdown(f"- Largura útil: **{_fmt_m(testada)} − {_fmt_m(rec_lat)} − {_fmt_m(rec_lat)} = {_fmt_m(largura_util)}**")
    st.markdown(f"- Profundidade útil: **{_fmt_m(profundidade)} − {_fmt_m(rec_front)} − {_fmt_m(rec_back)} = {_fmt_m(profund_util)}**")
    st.markdown(f"📐 **{_fmt_m(largura_util)} × {_fmt_m(profund_util)} = {_fmt_m2(area_recuos)}**")

    limite_terreo = min(area_to, area_recuos) if area_recuos > 0 else area_to

    st.markdown(
        f"👉 Nesse caso, mesmo podendo ocupar **{_fmt_m2(area_to)}** pela regra da zona, "
        f"o limite físico pelos recuos é **{_fmt_m2(area_recuos)}**."
    )
    st.markdown(f"**Limite recomendável no térreo (considerando TO e recuos): {_fmt_m2(limite_terreo)}**")

    # Opção 2: alinhamento (texto padrão)
    st.markdown("✅ **Opção 2 – Implantação no alinhamento (Art. 112 – LC 90/2023)**")
    st.markdown(
        "Por se tratar de **residência unifamiliar**, a legislação pode permitir zerar os recuos frontal e laterais, desde que:"
    )
    st.markdown("- Seja respeitada a **Taxa de Ocupação (TO)**")
    st.markdown("- Seja respeitada a **Taxa de Permeabilidade (TP)**")
    st.markdown(f"👉 Nesse caso, você pode utilizar: **{_fmt_m2(area_to)}** no térreo")
    st.markdown("⚠️ O recuo de fundo permanece obrigatório.")

    # 2) Permeabilidade
    st.markdown("🌿 **2️⃣ Quanto preciso deixar livre?**")
    if tp_min is None:
        st.warning("Sem Taxa de Permeabilidade (TP) mínima na regra do Supabase.")
    else:
        tp_min_pct = tp_min / 100.0 if tp_min > 1.0 else tp_min
        area_tp = lot_area * tp_min_pct
        st.markdown(f"A zona exige **{tp_min_pct*100:.0f}%** de área permeável.")
        st.markdown(f"👉 {_fmt_m2(lot_area)} × **{tp_min_pct*100:.0f}%** = **{_fmt_m2(area_tp)}** obrigatórios permeáveis")

        area_restante = max(lot_area - area_terreo_usada, 0.0)
        st.markdown(f"Se você utilizar **{_fmt_m2(area_terreo_usada)}** no térreo:")
        st.markdown(f"Área restante no lote: **{_fmt_m2(lot_area)} − {_fmt_m2(area_terreo_usada)} = {_fmt_m2(area_restante)}**")
        st.markdown("Desses:")
        st.markdown(f"- **{_fmt_m2(area_tp)}** devem permitir infiltração no solo")
        st.markdown(f"- **{_fmt_m2(max(area_restante - area_tp, 0.0))}** podem receber piso impermeável")

        st.markdown("🧱 **Tipos de piso e quanto contam como permeáveis (LC 90/2023 – Art. 108)**")
        st.markdown(
            """
| Tipo de Piso | Percentual considerado permeável |
|---|---:|
| Grama | 100% |
| Brita solta / terra batida | 100% |
| Piso drenante | 90% |
| Bloco de concreto vazado (“piso verde”) | 60% |
| Pedra portuguesa / intertravado | 25% |
"""
        )
        st.markdown("Isso significa que nem todo piso “externo” conta 100% como permeável.")

    # 3) IA e pavimentos
    st.markdown("🏢 **3️⃣ Posso construir mais andares?**")
    if ia_max is None:
        st.warning("Sem Índice de Aproveitamento (IA) máximo na regra do Supabase.")
    else:
        ia = ia_max
        area_total = lot_area * ia
        st.markdown("Além do limite no chão, existe o limite total permitido.")
        st.markdown(f"Índice de Aproveitamento (IA): **{ia:.2f}**")
        st.markdown(f"👉 {_fmt_m2(lot_area)} × **{ia:.2f}** = **{_fmt_m2(area_total)}** no total")
        st.markdown("Isso significa que você pode distribuir até esse total somando todos os pavimentos.")

    # 4) Estacionamento (texto padrão)
    st.markdown("🚗 **4️⃣ Estacionamento**")
    st.markdown(
        "De acordo com o **Anexo IV da LC 90/2023**, em geral não há previsão de quantidade mínima obrigatória de vagas para **residência unifamiliar**.\n\n"
        "A exigência de vagas aplica-se às residências multifamiliares e demais atividades listadas no Anexo IV."
    )
