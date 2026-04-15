from __future__ import annotations

import streamlit as st


def render_how_it_works_panel() -> None:
    with st.container():
        st.markdown(
            '''
            <div style="
                background:#ffffff;
                border:1px solid #e7e7e7;
                border-radius:14px;
                padding:20px 24px;
                margin-bottom:20px;
            ">
            ''',
            unsafe_allow_html=True,
        )

        st.markdown("### Como funciona")
        st.markdown("**1. Marque no mapa**  \nSelecione o terreno clicando no mapa.")
        st.markdown("**2. Preencha os dados**  \nInforme as dimensões do lote.")
        st.markdown("**3. Gere a viabilidade**  \nClique em **Gerar consulta aos índices urbanísticos**.")
        st.markdown("**4. Veja os resultados**  \nConfira zona, índices e análise.")
        st.markdown("**5. Gere o relatório (opcional)**  \nBaixe o relatório completo se quiser detalhamento.")

        st.markdown("</div>", unsafe_allow_html=True)
