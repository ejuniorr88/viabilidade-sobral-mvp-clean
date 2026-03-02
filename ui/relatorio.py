from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st


def _fmt_m(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return f"{v:.2f} m".replace(".", ",")


def _fmt_m2(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return f"{v:.2f} m²".replace(".", ",")


def _fmt_pct(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return f"{v:.1f}%".replace(".", ",")


def render_relatorio_section(
    *,
    calc: Dict[str, Any],
    lot_area: float,
    testada: Optional[float],
    profundidade: Optional[float],
    built_ground: float,
    area_permeavel_prevista_m2: float,
    to_max_pct: Optional[float],
    tp_min_pct: Optional[float],
    ia_max: Optional[float],
    pick_func,
    as_float_func,
    tipo_via: Optional[str] = None,
) -> None:
    st.subheader("🏡 RELATÓRIO URBANÍSTICO")

    zone = (calc or {}).get("zone") or "—"
    street_info = (calc or {}).get("street_info") or {}
    if not tipo_via:
        tipo_via = street_info.get("type") or "—"

    use_type_code = (calc or {}).get("use_type_code") or "—"

    # Recuos
    rule = (calc or {}).get("rule") or {}
    rec_frente = as_float_func(pick_func(rule, "recuo_frontal_m", "recuo_frente_m", "recuo_frente"))
    rec_fundo = as_float_func(pick_func(rule, "recuo_fundo_m", "recuo_fundos_m", "recuo_fundo"))
    rec_lateral = as_float_func(pick_func(rule, "recuo_lateral_m", "recuo_lateral"))

    # Cálculos principais
    to_max_m2 = (lot_area * (to_max_pct / 100.0)) if (lot_area > 0 and to_max_pct is not None) else None
    tp_min_m2 = (lot_area * (tp_min_pct / 100.0)) if (lot_area > 0 and tp_min_pct is not None) else None
    ia_total_m2 = (lot_area * ia_max) if (lot_area > 0 and ia_max is not None) else None

    # Opção 1: respeitando recuos (limite físico)
    largura_util = None
    prof_util = None
    area_implantavel_recuos = None
    if testada is not None and profundidade is not None and rec_lateral is not None and rec_frente is not None and rec_fundo is not None:
        largura_util = max(float(testada) - 2.0 * float(rec_lateral), 0.0)
        prof_util = max(float(profundidade) - float(rec_frente) - float(rec_fundo), 0.0)
        area_implantavel_recuos = largura_util * prof_util

    # Conclusão do térreo
    limite_terreo = None
    if to_max_m2 is not None and area_implantavel_recuos is not None:
        limite_terreo = min(to_max_m2, area_implantavel_recuos)
    elif to_max_m2 is not None:
        limite_terreo = to_max_m2
    elif area_implantavel_recuos is not None:
        limite_terreo = area_implantavel_recuos

    # Cabeçalho tipo ficha
    st.markdown(
        f"""**{use_type_code}**

Terreno: **{_fmt_m2(lot_area)}**
Dimensões: **{(f"{testada:.2f}".replace(".", ",") if testada is not None else "—")} m × {(f"{profundidade:.2f}".replace(".", ",") if profundidade is not None else "—")} m**
Zona: **{zone}**
Tipo: **{tipo_via}**
"""
    )

    st.markdown("---")

    # 1) Quanto pode ocupar no chão
    st.markdown("### 📍 1️⃣ Quanto posso ocupar no chão?")
    if to_max_pct is None or to_max_m2 is None:
        st.info("Não foi possível calcular a Taxa de Ocupação (TO) porque o valor não veio do Supabase.")
    else:
        st.markdown(
            f"""A zona permite ocupar até **{_fmt_pct(to_max_pct)}** do terreno no térreo.

👉 **{_fmt_m2(lot_area)} × {to_max_pct:.1f}% = {_fmt_m2(to_max_m2)}**

Esse é o limite máximo permitido pela **Taxa de Ocupação**.
"""
        )

        st.markdown("Agora veja duas situações possíveis:")

        # Opção 1
        st.markdown("#### ✅ Opção 1 – Respeitando os recuos padrão")
        if rec_frente is None or rec_lateral is None or rec_fundo is None or area_implantavel_recuos is None:
            st.warning("Não foi possível calcular a área interna pelos recuos porque falta algum recuo/dimensão.")
        else:
            st.markdown(
                f"""Recuos exigidos:

- Frontal: **{_fmt_m(rec_frente)}**
- Laterais: **{_fmt_m(rec_lateral)}** cada
- Fundo: **{_fmt_m(rec_fundo)}**

Área interna disponível:

**Largura útil:**  
{testada:.2f} − {rec_lateral:.2f} − {rec_lateral:.2f} = **{largura_util:.2f} m**

**Profundidade útil:**  
{profundidade:.2f} − {rec_frente:.2f} − {rec_fundo:.2f} = **{prof_util:.2f} m**

📐 **{largura_util:.2f} × {prof_util:.2f} = {_fmt_m2(area_implantavel_recuos)}**

👉 Nesse caso, mesmo podendo ocupar {_fmt_m2(to_max_m2)} pela regra da zona,  
o limite físico pelos recuos é **{_fmt_m2(area_implantavel_recuos)}**.
""".replace(".", ",")
            )

        # Opção 2 (texto – regra específica pode ser refinada depois)
        st.markdown("#### ✅ Opção 2 – Implantação no alinhamento (Art. 112 – LC 90/2023)")
        st.markdown(
            f"""Para alguns casos (ex.: residência unifamiliar), a legislação pode permitir **zerar recuos frontal e laterais**, desde que:

- Seja respeitada a **Taxa de Ocupação**
- Seja respeitada a **Taxa de Permeabilidade**

Nesse caso, você pode utilizar:

👉 **{_fmt_m2(to_max_m2)}** no térreo

⚠ O recuo de fundo permanece obrigatório (quando aplicável)."""
        )

    # 2) Área livre / permeável
    st.markdown("### 🌿 2️⃣ Quanto preciso deixar livre?")
    if tp_min_pct is None or tp_min_m2 is None:
        st.info("Não foi possível calcular a Taxa de Permeabilidade (TP) porque o valor não veio do Supabase.")
    else:
        st.markdown(
            f"""A zona exige **{_fmt_pct(tp_min_pct)}** de área permeável.

👉 **{_fmt_m2(lot_area)} × {tp_min_pct:.1f}% = {_fmt_m2(tp_min_m2)}** obrigatórios permeáveis"""
        )

        area_restante = max(lot_area - built_ground, 0.0)
        st.markdown(
            f"""Se você utilizar **{_fmt_m2(built_ground)}** no térreo:

Área restante no lote:  
**{_fmt_m2(lot_area)} − {_fmt_m2(built_ground)} = {_fmt_m2(area_restante)}**

Área permeável informada: **{_fmt_m2(area_permeavel_prevista_m2)}**
"""
        )

        st.markdown(
            """🧱 **Tipos de piso e quanto contam como permeáveis** (LC 90/2023 – Art. 108)

| Tipo de Piso | Percentual considerado permeável |
|---|---:|
| Grama | 100% |
| Brita solta / terra batida | 100% |
| Piso drenante | 90% |
| Bloco de concreto vazado (“piso verde”) | 60% |
| Pedra portuguesa / intertravado | 25% |

Isso significa que nem todo piso “externo” conta 100% como permeável.
"""
        )

    # 3) total por IA / pavimentos
    st.markdown("### 🏢 3️⃣ Posso construir mais andares?")
    if ia_max is None or ia_total_m2 is None:
        st.info("Não foi possível calcular o total por IA porque o valor não veio do Supabase.")
    else:
        altura_max = as_float_func(pick_func(rule, "altura_max_m", "gabarito_m", "altura_maxima_m", "altura_max"))
        st.markdown(
            f"""Além do limite no chão, existe o limite total permitido.

Índice de Aproveitamento (IA): **{ia_max:.2f}**

👉 **{_fmt_m2(lot_area)} × {ia_max:.2f} = {_fmt_m2(ia_total_m2)}** no total

Isso significa que você pode distribuir até **{_fmt_m2(ia_total_m2)}** somando todos os pavimentos.
""".replace(".", ",")
        )
        if altura_max is not None:
            st.markdown(f"Altura máxima da zona: **{_fmt_m(altura_max)}**")
            st.markdown("Essa altura normalmente comporta cerca de **3 pavimentos** confortáveis, dependendo do projeto.")
