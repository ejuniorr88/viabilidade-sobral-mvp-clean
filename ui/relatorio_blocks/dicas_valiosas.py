from __future__ import annotations

import streamlit as st


def get_dicas_valiosas(is_corner: bool = False) -> list[tuple[str, str]]:
    dicas = [
        (
            "Passeios (calçadas)",
            "Não há, na legislação municipal, uma medida única e fixa para a largura dos passeios. Quando existir, deve-se adotar o padrão definido no projeto aprovado do loteamento e/ou nas diretrizes urbanísticas da via; na ausência dessa previsão, utiliza-se como referência o passeio já implantado no logradouro, garantindo continuidade e alinhamento, sendo a análise do licenciamento voltada a confirmar que a proposta não avança sobre a área pública.",
        ),
        (
            "Piscinas",
            "Se for construída uma piscina, ela não é computada como área construída e, por isso, não entra no cálculo da Taxa de Ocupação (TO). Porém, para a Taxa de Permeabilidade (TP), a piscina é considerada área impermeável, reduzindo a área permeável do lote. Além disso, conforme o Art. 144, piscinas, espelhos d’água, caixas d’água, cisternas e tanques devem manter afastamento mínimo de 0,50 m de todas as divisas do terreno e sempre ser computados como área impermeável no cálculo da TP.",
        ),
    ]
    if is_corner:
        dicas.append(("Texto temporário — lote de esquina", "Texto a ser escrito."))
    return dicas


def render_dicas_valiosas(is_corner: bool = False) -> None:
    st.markdown("#### 💡 Dicas Valiosas:")
    for titulo, texto in get_dicas_valiosas(is_corner=is_corner):
        st.markdown(f"• **{titulo}:** {texto}")
