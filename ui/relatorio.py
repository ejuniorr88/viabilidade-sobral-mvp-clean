from __future__ import annotations

from typing import Any, Dict, Optional, Callable

import streamlit as st


def _to_float(v: Any) -> float:
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return 0.0
        s = s.replace(".", "")
        s = s.replace(",", ".")
        try:
            return float(s)
        except Exception:
            return 0.0
    try:
        return float(v)
    except Exception:
        return 0.0


def _as_float(x: Any) -> Optional[float]:
    try:
        return float(x)
    except Exception:
        return None


def _fmt_m2(v: float) -> str:
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m²"


def _fmt_m(v: float) -> str:
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m"


def render_relatorio_section(*, lot_area, frontage, depth, zone_sigla, via_tipo, use_type_code, rule, area_terreo=None, area_permeavel_prevista=None, pick_func=None, **kwargs):
    if pick_func is None:
        pick_func = lambda r,*ks: next((r.get(k) for k in ks if isinstance(r, dict) and r.get(k) not in (None,'')), None)
    *,
    calc: Dict[str, Any],
    lot_area: Any,
    testada: Any,
    profundidade: Any,
    built_ground: Any,
    area_permeavel_prevista: Any,
    pick_func: Callable[..., Any],
):
    st.subheader("6) Relatório Urbanístico")

    if not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar o relatório.")
        return

    rule = calc.get("rule")
    if not rule:
        st.info("Sem regra do Supabase — não é possível gerar relatório.")
        return

    lot_area_f = _to_float(lot_area)
    testada_f = _to_float(testada)
    profund_f = _to_float(profundidade)
    built_ground_f = _to_float(built_ground)
    area_perm_f = _to_float(area_permeavel_prevista)

    zone = calc.get("zone") or "—"
    use_type = calc.get("use_type_code") or "—"
    via_tipo = (calc.get("street_info") or {}).get("tipo_via") or "via local"

    to_max = _as_float(pick_func(rule, "to_max_pct", "to_max"))
    ia_max = _as_float(pick_func(rule, "ia_max", "ia_maximo"))
    tp_min = _as_float(pick_func(rule, "tp_min_pct", "tp_min"))

    rec_frente = _as_float(pick_func(rule, "recuo_frontal_m", "front_setback_m", "recuo_frontal")) or 0.0
    rec_lateral = _as_float(pick_func(rule, "recuo_lateral_m", "side_setback_m", "recuo_lateral")) or 0.0
    rec_fundo = _to_float(pick_func(rule, 'recuo_fundo_m', 'recuo_fundos_m', 'recuo_fundo', 'recuo_fundos'))

    # Se não informar área pretendida, assumir máximo da TO
    if (built_ground_f <= 0) and (to_max is not None) and lot_area_f > 0:
        built_ground_f = (lot_area_f * to_max) / 100.0

    # ===== Cabeçalho =====
    st.markdown("🏡 **RELATÓRIO URBANÍSTICO**")
    st.markdown(f"**{use_type}**")

    st.write(f"**Terreno:** {_fmt_m2(lot_area_f)}")
    st.write(f"**Dimensões:** {_fmt_m(testada_f)} × {_fmt_m(profund_f)}")
    st.write(f"**Zona:** {zone}")
    st.write(f"**Tipo:** {via_tipo}")

    st.markdown("---")

    # ===== 1) Quanto posso ocupar no chão? =====
    st.markdown("📍 **1️⃣ Quanto posso ocupar no chão?**")

    if to_max is not None:
        max_to_area = (lot_area_f * to_max) / 100.0
        st.write(f"A zona permite ocupar até **{to_max:.0f}%** do terreno no térreo.")
        st.write(f"👉 {_fmt_m2(lot_area_f)} × {to_max:.0f}% = **{_fmt_m2(max_to_area)}**")
        st.write("Esse é o limite máximo permitido pela **Taxa de Ocupação (TO)**.")
    else:
        max_to_area = 0.0
        st.warning("TO máxima não encontrada na regra.")

    st.write("Agora veja duas situações possíveis:")

    # ===== Opção 1 =====
    st.markdown("✅ **Opção 1 – Respeitando os recuos padrão**")
    st.write("**Recuos exigidos:**")
    st.write(f"- Frontal: **{_fmt_m(rec_frente)}**")
    st.write(f"- Laterais: **{_fmt_m(rec_lateral)}** cada")
    st.write(f"- Fundo: **{_fmt_m(rec_fundo)}**")

    if testada_f > 0 and profund_f > 0:
        largura_util = max(testada_f - 2 * rec_lateral, 0.0)
        prof_util = max(profund_f - rec_frente - rec_fundo, 0.0)
        area_interna = largura_util * prof_util
        st.write("**Área interna disponível:**")
        st.write(f"- Largura útil: {testada_f:.2f} − {rec_lateral:.2f} − {rec_lateral:.2f} = **{largura_util:.2f} m**")
        st.write(f"- Profundidade útil: {profund_f:.2f} − {rec_frente:.2f} − {rec_fundo:.2f} = **{prof_util:.2f} m**")
        st.write(f"📐 **{largura_util:.2f} × {prof_util:.2f} = {area_interna:.2f} m²**")

        if max_to_area > 0:
            limite = min(max_to_area, area_interna)
            if area_interna < max_to_area:
                st.write(
                    f"👉 Nesse caso, mesmo podendo ocupar **{max_to_area:.2f} m²** pela regra da zona, "
                    f"o limite físico pelos recuos é **{area_interna:.2f} m²**."
                )
            else:
                st.write(
                    f"👉 Nesse caso, o limite dos recuos permite até **{area_interna:.2f} m²**, "
                    f"mas o teto da TO limita em **{max_to_area:.2f} m²**."
                )
    else:
        st.info("Não foi possível calcular a área interna pelos recuos (testada/profundidade ausentes).")

    # ===== Opção 2 =====
    st.markdown("✅ **Opção 2 – Implantação no alinhamento (Art. 112 – LC 90/2023)**")
    st.write(
        "Por se tratar de **residência unifamiliar**, a legislação pode permitir zerar os recuos frontal e laterais, desde que:"
    )
    st.write("- Seja respeitada a **Taxa de Ocupação (TO)**")
    st.write("- Seja respeitada a **Taxa de Permeabilidade (TP)**")
    st.write("⚠️ O **recuo de fundo** permanece obrigatório.")

    if max_to_area > 0:
        st.write(f"Nesse caso, você pode utilizar: 👉 **{_fmt_m2(max_to_area)}** no térreo")

    st.markdown("---")

    # ===== 2) Área permeável =====
    st.markdown("🌿 **2️⃣ Quanto preciso deixar livre?**")
    if tp_min is not None and lot_area_f > 0:
        area_perm_min = (lot_area_f * tp_min) / 100.0
        st.write(f"A zona exige **{tp_min:.0f}%** de área permeável.")
        st.write(f"👉 {_fmt_m2(lot_area_f)} × {tp_min:.0f}% = **{_fmt_m2(area_perm_min)}** obrigatórios permeáveis")

        if max_to_area > 0:
            area_restante = lot_area_f - max_to_area
            st.write(f"Se você utilizar **{_fmt_m2(max_to_area)}** no térreo:")
            st.write(f"- Área restante no lote: {_fmt_m2(lot_area_f)} − {_fmt_m2(max_to_area)} = **{_fmt_m2(area_restante)}**")
            st.write(f"- Desses: **{_fmt_m2(area_perm_min)}** devem permitir infiltração no solo")
            st.write(f"- **{_fmt_m2(max(area_restante - area_perm_min, 0.0))}** podem receber piso impermeável")

        if area_perm_f > 0:
            tp_prev = (area_perm_f / lot_area_f) * 100.0
            if tp_prev + 1e-9 >= tp_min:
                st.success(f"✅ TP prevista: {tp_prev:.1f}% (atende o mínimo)")
            else:
                st.warning(f"⚠️ TP prevista: {tp_prev:.1f}% (abaixo do mínimo)")
    else:
        st.info("TP mínima não encontrada na regra.")

    st.markdown(
        """
**Tipos de piso e quanto contam como permeáveis (LC 90/2023 – Art. 108)**

| Tipo de Piso | % considerado permeável |
|---|---:|
| Grama | 100% |
| Brita solta / terra batida | 100% |
| Piso drenante | 90% |
| Bloco de concreto vazado (“piso verde”) | 60% |
| Pedra portuguesa / intertravado | 25% |

*Nem todo piso “externo” conta 100% como permeável.*
"""
    )

    st.markdown("---")

    # ===== 3) IA / altura =====
    st.markdown("🏢 **3️⃣ Posso construir mais andares?**")
    if ia_max is not None and lot_area_f > 0:
        max_total = lot_area_f * ia_max
        st.write("Além do limite no chão, existe o limite total permitido.")
        st.write(f"**Índice de Aproveitamento (IA): {ia_max}**")
        st.write(f"👉 {_fmt_m2(lot_area_f)} × {ia_max} = **{_fmt_m2(max_total)}** no total")
        st.write("Isso significa que você pode distribuir essa área somando todos os pavimentos.")
    else:
        st.info("IA máximo não encontrado na regra.")

    altura_max = _as_float(pick_func(rule, "altura_max_m", "altura_max", "gabarito_m"))
    if altura_max is not None:
        st.write(f"**Altura máxima da zona:** {altura_max:.0f} m")

    st.markdown("---")

    # ===== 4) Estacionamento (placeholder) =====
    st.markdown("🚗 **4️⃣ Estacionamento**")
    st.write(
        "De acordo com o Anexo IV da LC 90/2023, em geral não há previsão de vagas mínimas para residência unifamiliar; "
        "a exigência costuma recair sobre multifamiliar e outras atividades listadas."
    )

    st.markdown("---")

    # ===== Quadro técnico (placeholder) =====
    st.markdown("🧾 **QUADRO TÉCNICO – PARÂMETROS DOS AMBIENTES (LC 90/2023 – Anexo II)**")
    st.markdown(
        """
| AMBIENTE | CÍRCULO INSCRITO | ÁREA MÍNIMA | ILUMINAÇÃO | VENTILAÇÃO | PÉ-DIREITO | OBS. |
|---|---:|---:|---:|---:|---:|---|
| Sala de estar | 2,00 m | 8,00 m² | 1/8 | 1/12 | 2,50 m | 7 |
| Sala de jantar | 2,00 m | 6,00 m² | 1/8 | 1/12 | 2,50 m | 7 |
| Cozinha | 1,80 m | 5,00 m² | 1/8 | 1/12 | 2,50 m | 1-7 |
| 1º e 2º quartos | 2,00 m | 8,00 m² | 1/8 | 1/12 | 2,50 m | — |
| Demais quartos | 2,00 m | 5,00 m² | 1/8 | 1/12 | 2,50 m | — |
| Banheiro | 1,00 m | 1,50 m² | 1/10 | 1/16 | 2,20 m | 1-2-3 |
| Área de serviço | 1,20 m | 1,80 m² | 1/10 | 1/16 | 2,20 m | 1-2-7 |
| Garagem | 2,20 m | 9,00 m² | 1/14 | 1/24 | 2,20 m | 7 |
| Escada | 0,80 m | — | — | — | 2,10 m | 8-11-12-13 |

**Observações aplicáveis (Anexo II – LC 90/2023)**
- Tolera-se iluminação e ventilação zenital.
- Admite-se ventilação mecânica ou indireta nos casos permitidos.
- Banheiro não pode comunicar-se diretamente com cozinha ou sala de jantar.
- Corredores com mais de 5,00 m devem ter largura mínima de 1,00 m.
- Patamar obrigatório quando houver mudança de direção ou altura superior a 2,90 m.
- Largura mínima do degrau: 0,25 m. Altura máxima do degrau: 0,19 m.
"""
    )
