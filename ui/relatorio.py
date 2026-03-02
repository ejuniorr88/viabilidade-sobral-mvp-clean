from __future__ import annotations

from typing import Any, Dict, Callable, Optional
import streamlit as st


def _to_float(x: Any) -> Optional[float]:
    try:
        if x is None or x == "":
            return None
        return float(x)
    except Exception:
        return None


def _fmt_m2(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m²"


def _fmt_m(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m"


def _fmt_pct(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return f"{v:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".") + "%"


def render_relatorio_section(
    *,
    calc: Dict[str, Any],
    lot_area: float,
    testada: float,
    profundidade: float,
    built_ground: float,
    pick_func: Callable[[Dict[str, Any], str], Any],
) -> None:
    st.subheader("6) Relatório Urbanístico")

    if not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar o relatório.")
        return

    rule = calc.get("rule")
    if not rule:
        st.info("Sem regra do Supabase — não é possível montar o relatório.")
        return

    zone = calc.get("zone") or "—"
    street_info = calc.get("street_info") or {}
    tipo_via = street_info.get("type") or "—"

    use_type_code = calc.get("use_type_code") or "RES_UNI"

    # Regras (puxar pelos nomes mais comuns no dump)
    to_max_pct = _to_float(pick_func(rule, "to_max_pct", "to_max", "taxa_ocupacao_max_pct"))
    tp_min_pct = _to_float(pick_func(rule, "tp_min_pct", "tp_min", "taxa_permeabilidade_min_pct"))
    ia_max = _to_float(pick_func(rule, "ia_max", "ia_maximo", "indice_aproveitamento_max"))
    altura_max_m = _to_float(pick_func(rule, "altura_max_m", "gabarito_m", "altura_maxima_m", "altura_max"))

    rec_frente = _to_float(pick_func(rule, "recuo_frontal_m", "recuo_frente_m", "recuo_frente"))
    rec_fundo = _to_float(pick_func(rule, "recuo_fundo_m", "recuo_fundos_m", "recuo_fundo"))
    rec_lateral = _to_float(pick_func(rule, "recuo_lateral_m", "recuo_lateral"))

    # --- 1) Quanto posso ocupar no chão?
    # Se o usuário não informar área pretendida, assume o máximo permitido pela TO.
    area_to_max = (lot_area * (to_max_pct / 100.0)) if (to_max_pct is not None) else None
    area_terreo_base = built_ground if (built_ground and built_ground > 0) else area_to_max

    # Opção 1: com recuos padrão (limite físico)
    area_recuos = None
    if rec_frente is not None and rec_fundo is not None and rec_lateral is not None:
        largura_util = max(0.0, testada - 2.0 * rec_lateral)
        prof_util = max(0.0, profundidade - rec_frente - rec_fundo)
        area_recuos = largura_util * prof_util
    else:
        largura_util = None
        prof_util = None

    # Limite final no térreo: o menor entre TO e recuos (se ambos existirem)
    if area_to_max is not None and area_recuos is not None:
        area_terreo_max_com_recuos = min(area_to_max, area_recuos)
    else:
        area_terreo_max_com_recuos = area_recuos if area_recuos is not None else area_to_max

    # Opção 2: alinhamento (residência unifamiliar) — zera frente e laterais, mantém fundo
    area_alinhamento = None
    if rec_fundo is not None:
        area_alinhamento = max(0.0, testada * max(0.0, profundidade - rec_fundo))

    if area_to_max is not None and area_alinhamento is not None:
        area_terreo_max_alinhamento = min(area_to_max, area_alinhamento)
    else:
        area_terreo_max_alinhamento = area_alinhamento if area_alinhamento is not None else area_to_max

    # --- 2) Permeabilidade
    area_perm_min = (lot_area * (tp_min_pct / 100.0)) if (tp_min_pct is not None) else None

    # --- 3) Total construível (IA)
    area_total_max = (lot_area * ia_max) if (ia_max is not None) else None

    # Render (texto no estilo do exemplo do usuário)
    st.markdown(
        f"""
🏡 **RELATÓRIO URBANÍSTICO**  
**{use_type_code}**

**Terreno:** {_fmt_m2(lot_area)}  
**Dimensões:** {_fmt_m(testada)} × {_fmt_m(profundidade)}  
**Zona:** **{zone}**  
**Tipo:** {tipo_via}
"""
    )

    st.markdown("📍 **1️⃣ Quanto posso ocupar no chão?**")

    if to_max_pct is None or area_to_max is None:
        st.warning("Não encontrei a **Taxa de Ocupação (TO)** no Supabase para este caso.")
    else:
        st.markdown(
            f"""
A zona permite ocupar até **{_fmt_pct(to_max_pct)}** do terreno no térreo.

👉 **{_fmt_m2(lot_area)} × {_fmt_pct(to_max_pct)} = {_fmt_m2(area_to_max)}**

Esse é o limite máximo permitido pela **Taxa de Ocupação**.
"""
        )

        st.markdown("Agora veja duas situações possíveis:")

        st.markdown("✅ **Opção 1 – Respeitando os recuos padrão**")

        if area_recuos is None or largura_util is None or prof_util is None:
            st.info("Não há recuos suficientes no Supabase para calcular a área útil interna por recuos.")
        else:
            st.markdown(
                f"""
**Recuos exigidos:**  
- Frontal: **{_fmt_m(rec_frente)}**  
- Laterais: **{_fmt_m(rec_lateral)}** cada  
- Fundo: **{_fmt_m(rec_fundo)}**

**Área interna disponível (limitada pelos recuos):**

Largura útil:  
**{testada:.2f} − {rec_lateral:.2f} − {rec_lateral:.2f} = {largura_util:.2f} m**

Profundidade útil:  
**{profundidade:.2f} − {rec_frente:.2f} − {rec_fundo:.2f} = {prof_util:.2f} m**

📐 **{largura_util:.2f} × {prof_util:.2f} = {area_recuos:,.2f} m²**
""".replace(",", "X").replace(".", ",").replace("X", ".")
            )

            if area_terreo_max_com_recuos is not None:
                st.markdown(
                    f"""
👉 Nesse caso, mesmo podendo ocupar **{_fmt_m2(area_to_max)}** pela regra da zona,  
o limite final no térreo fica em **{_fmt_m2(area_terreo_max_com_recuos)}** (o menor entre TO e recuos).
"""
                )

        st.markdown("✅ **Opção 2 – Implantação no alinhamento (Art. 112 – LC 90/2023)**")
        st.markdown(
            """
Por se tratar de **residência unifamiliar**, a legislação pode permitir zerar os recuos **frontal e laterais**,
desde que:

- Seja respeitada a **Taxa de Ocupação**
- Seja respeitada a **Taxa de Permeabilidade**

⚠ O **recuo de fundo** permanece obrigatório.
"""
        )

        if area_terreo_max_alinhamento is not None:
            st.markdown(f"👉 Nesse cenário, você pode utilizar até **{_fmt_m2(area_terreo_max_alinhamento)}** no térreo.")

    st.markdown("🌿 **2️⃣ Quanto preciso deixar livre?**")
    if area_perm_min is None or tp_min_pct is None:
        st.warning("Não encontrei a **Taxa de Permeabilidade (TP)** no Supabase para este caso.")
    else:
        st.markdown(
            f"""
A zona exige **{_fmt_pct(tp_min_pct)}** de área permeável.

👉 **{_fmt_m2(lot_area)} × {_fmt_pct(tp_min_pct)} = {_fmt_m2(area_perm_min)}** obrigatórios permeáveis
"""
        )

        # Se o usuário não informou built_ground, usa o máximo (alinhamento como melhor aproveitamento)
        area_terreo_para_conta = area_terreo_base if area_terreo_base is not None else 0.0
        area_restante = max(0.0, lot_area - area_terreo_para_conta)
        area_imperm_possivel = max(0.0, area_restante - area_perm_min)

        st.markdown(
            f"""
Se você utilizar **{_fmt_m2(area_terreo_para_conta)}** no térreo:

Área restante no lote:  
**{_fmt_m2(lot_area)} − {_fmt_m2(area_terreo_para_conta)} = {_fmt_m2(area_restante)}**

Desses:
- **{_fmt_m2(area_perm_min)}** devem permitir infiltração no solo  
- **{_fmt_m2(area_imperm_possivel)}** podem receber piso impermeável
"""
        )

        st.markdown(
            """
🧱 **Tipos de piso e quanto contam como permeáveis** *(LC 90/2023 – Art. 108)*

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

    st.markdown("🏢 **3️⃣ Posso construir mais andares?**")
    if area_total_max is None or ia_max is None:
        st.warning("Não encontrei o **Índice de Aproveitamento (IA)** no Supabase para este caso.")
    else:
        st.markdown(
            f"""
Além do limite no chão, existe o limite total permitido.

**Índice de Aproveitamento (IA): {ia_max:.2f}**

👉 **{_fmt_m2(lot_area)} × {ia_max:.2f} = {_fmt_m2(area_total_max)}** no total

Isso significa que você pode distribuir até **{_fmt_m2(area_total_max)}** somando todos os pavimentos.
"""
        )

    if altura_max_m is not None:
        st.markdown(f"**Altura máxima da zona:** **{_fmt_m(altura_max_m)}**")
        st.caption("A quantidade de pavimentos depende do projeto (pé-direito, cobertura, etc.).")

    st.markdown("🚗 **4️⃣ Estacionamento**")
    st.markdown(
        """
De acordo com o **Anexo IV da LC 90/2023**, em geral **não há previsão de vagas mínimas para residência unifamiliar**.
A exigência costuma aplicar-se a residências multifamiliares e demais atividades listadas no Anexo IV.
"""
    )

    st.caption("Obs.: este relatório é automático e serve como apoio inicial. Para casos especiais, confira a legislação e exceções da zona/uso.")
