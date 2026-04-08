from __future__ import annotations

import streamlit as st


def render_how_it_works_panel() -> None:
    st.markdown(
        """
        <div style="
            background:#ffffff;
            border:1px solid #e7e7e7;
            border-radius:14px;
            padding:20px 24px;
            margin-bottom:20px;
        ">
            <h3 style="margin:0 0 14px 0;color:#1f2a44;">Como funciona</h3>

            <p style="margin:0 0 10px 0;">
                <b>1. Marque no mapa</b><br>
                Selecione o terreno clicando no mapa.
            </p>

            <p style="margin:0 0 10px 0;">
                <b>2. Preencha os dados</b><br>
                Informe as dimensões do lote.
            </p>

            <p style="margin:0 0 10px 0;">
                <b>3. Gere a viabilidade</b><br>
                Clique em <b>Gerar estudo de viabilidade</b>.
            </p>

            <p style="margin:0 0 10px 0;">
                <b>4. Veja os resultados</b><br>
                Confira zona, índices e análise.
            </p>

            <p style="margin:0;">
                <b>5. Gere o relatório (opcional)</b><br>
                Baixe o relatório completo se quiser detalhamento.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
