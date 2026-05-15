from __future__ import annotations

from typing import List

import streamlit as st


def get_dicas_valiosas(is_corner: bool = False) -> List[str]:
    dicas = [
        "**Passeios (calçadas):** Não há, na legislação municipal, uma medida única e fixa para a largura dos passeios. "
        "Quando existir, deve-se adotar o padrão definido no projeto aprovado do loteamento e/ou nas diretrizes urbanísticas da via; "
        "na ausência dessa previsão, utiliza-se como referência o passeio já implantado no logradouro, garantindo continuidade e alinhamento, "
        "sendo a análise do licenciamento voltada a confirmar que a proposta não avança sobre a área pública.",
        "**Atenção:** para a Taxa de Ocupação (TO), a piscina não é contada como área construída do lote.",
        "**Art. 144.** As piscinas, espelhos d’água, caixas d’água, cisternas e tanques deverão observar um afastamento mínimo de 0,50 m "
        "de todas as divisas do terreno e devem ser computados como área impermeável para o cálculo da **Taxa de Permeabilidade (TP)**.",
        "👉 **Na prática:** além de respeitar esse afastamento mínimo de 50 cm, esses elementos também entram no cálculo da Taxa de Permeabilidade (TP) como área impermeável.",
    ]
    if is_corner:
        dicas.append("**Texto temporário – lote de esquina**")
    return dicas


def render_dicas_valiosas(is_corner: bool = False) -> None:
    st.markdown("### 💡 1️⃣2️⃣ Dicas valiosas")
    st.markdown("**Dicas Valiosas**")

    st.markdown("**Flexibilidade de recuos no uso residencial unifamiliar**")
    st.markdown(
        "**Art. 112.** Será aplicado, para as atividades atrativas de vizinhança de pequeno porte e para o uso residencial unifamiliar, "
        "a flexibilidade quanto aos recuos de frente e laterais, podendo zerar, desde que observado o cumprimento da Taxa de Permeabilidade "
        "Mínima e da Taxa de Ocupação Máxima da zona em que se encontra."
    )
    st.markdown(
        "👉 **Na prática:** para residência unifamiliar, a legislação admite zerar recuos frontal e laterais, "
        "desde que a proposta continue respeitando a Taxa de Permeabilidade (TP) mínima e a Taxa de Ocupação (TO) máxima da zona."
    )

    st.markdown("**Passeios (calçadas)**")
    st.markdown(
        "Não há, na legislação municipal, uma medida única e fixa para a largura dos passeios. Quando existir, deve-se adotar o padrão "
        "definido no projeto aprovado do loteamento e/ou nas diretrizes urbanísticas da via; na ausência dessa previsão, utiliza-se "
        "como referência o passeio já implantado no logradouro."
    )

    st.markdown("**Piscinas, espelhos d’água, caixas d’água, cisternas e tanques**")
    for dica in get_dicas_valiosas(is_corner=is_corner):
        st.markdown(dica)
