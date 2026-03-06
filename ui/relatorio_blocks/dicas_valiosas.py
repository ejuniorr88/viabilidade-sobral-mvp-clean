from __future__ import annotations

import streamlit as st


def render_dicas_valiosas() -> None:
    st.markdown("#### 💡 Dicas Valiosas:")
    st.markdown(
        "• **Passeios (calçadas):** Não há, na legislação municipal, uma medida única e fixa para a largura dos passeios. "
        "Quando existir, deve-se adotar o padrão definido no projeto aprovado do loteamento e/ou nas diretrizes urbanísticas da via; "
        "na ausência dessa previsão, utiliza-se como referência o passeio já implantado no logradouro, garantindo continuidade e alinhamento, "
        "sendo a análise do licenciamento voltada a confirmar que a proposta não avança sobre a área pública."
    )
    st.markdown(
        "• **Piscinas:** Se for construída uma piscina, ela não é computada como área construída e, por isso, não entra no cálculo da Taxa de Ocupação (TO). "
        "Porém, para a Taxa de Permeabilidade (TP), a piscina é considerada área impermeável, reduzindo a área permeável do lote. "
        "Além disso, conforme o Art. 144, piscinas, espelhos d’água, caixas d’água, cisternas e tanques devem manter afastamento mínimo de 0,50 m de todas as divisas "
        "do terreno e sempre ser computados como área impermeável no cálculo da TP."
    )

