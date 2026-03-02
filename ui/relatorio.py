from __future__ import annotations
import streamlit as st


def render_relatorio(
    zone: str,
    lot_area: float,
    testada: float,
    profundidade: float,
    rule: dict,
    built_ground: float,
):

    if not rule:
        return

    # ===== PARÂMETROS =====
    to_max = rule.get("to_max_pct") or 0
    tp_min = rule.get("tp_min_pct") or 0
    ia_max = rule.get("ia_max") or 0
    altura_max = rule.get("altura_max_m") or rule.get("gabarito_m") or 0

    rec_frente = rule.get("recuo_frontal_m") or rule.get("recuo_frente_m") or 0
    rec_fundo = rule.get("recuo_fundo_m") or 0
    rec_lateral = rule.get("recuo_lateral_m") or 0

    # ===== CÁLCULOS =====
    ocupacao_max_m2 = lot_area * (to_max / 100)
    area_permeavel_obrig = lot_area * (tp_min / 100)
    area_total_max = lot_area * ia_max

    largura_util = testada - (rec_lateral * 2)
    profundidade_util = profundidade - rec_frente - rec_fundo

    area_recuos = 0
    if largura_util > 0 and profundidade_util > 0:
        area_recuos = largura_util * profundidade_util

    restante_lote = lot_area - ocupacao_max_m2

    # ===== RELATÓRIO =====

    st.markdown("## 🏡 RELATÓRIO URBANÍSTICO")
    st.markdown("### Residencial Unifamiliar")

    st.markdown(f"""
Terreno: **{lot_area:.2f} m²**  
Dimensões: **{testada:.2f} m × {profundidade:.2f} m**  
Zona: **{zone}**
""")

    st.markdown("---")

    # ========================
    # 1️⃣ OCUPAÇÃO
    # ========================
    st.markdown("## 📍 1️⃣ Quanto posso ocupar no chão?")

    st.markdown(f"""
A zona permite ocupar até **{to_max:.0f}%** do terreno no térreo.

👉 {lot_area:.2f} × {to_max:.0f}% = **{ocupacao_max_m2:.2f} m²**
""")

    st.markdown("### ✅ Respeitando os recuos padrão")

    st.markdown(f"""
Recuos exigidos:

Frontal: **{rec_frente:.2f} m**  
Laterais: **{rec_lateral:.2f} m cada**  
Fundo: **{rec_fundo:.2f} m**

Largura útil:
{testada:.2f} − {rec_lateral:.2f} − {rec_lateral:.2f} = **{largura_util:.2f} m**

Profundidade útil:
{profundidade:.2f} − {rec_frente:.2f} − {rec_fundo:.2f} = **{profundidade_util:.2f} m**

📐 {largura_util:.2f} × {profundidade_util:.2f} = **{area_recuos:.2f} m²**
""")

    if area_recuos > 0:
        if area_recuos < ocupacao_max_m2:
            st.info("👉 O limite físico pelos recuos é menor que o permitido pela zona.")
        else:
            st.info("👉 O limite real passa a ser a Taxa de Ocupação da zona.")

    st.markdown("---")

    # ========================
    # 2️⃣ PERMEABILIDADE
    # ========================
    st.markdown("## 🌿 2️⃣ Quanto preciso deixar livre?")

    st.markdown(f"""
A zona exige **{tp_min:.0f}%** de área permeável.

👉 {lot_area:.2f} × {tp_min:.0f}% = **{area_permeavel_obrig:.2f} m² obrigatórios**
""")

    st.markdown(f"""
Se utilizar o máximo de {ocupacao_max_m2:.2f} m² no térreo:

Área restante:
{lot_area:.2f} − {ocupacao_max_m2:.2f} = **{restante_lote:.2f} m²**
""")

    st.markdown("---")

    # ========================
    # 3️⃣ IA
    # ========================
    st.markdown("## 🏢 3️⃣ Posso construir mais andares?")

    st.markdown(f"""
Índice de Aproveitamento (IA): **{ia_max:.2f}**

👉 {lot_area:.2f} × {ia_max:.2f} = **{area_total_max:.2f} m² no total**
""")

    if altura_max:
        st.markdown(f"Altura máxima permitida: **{altura_max:.2f} m**")

    st.markdown("---")

    st.success("Relatório gerado automaticamente com base nos parâmetros do zoneamento.")
