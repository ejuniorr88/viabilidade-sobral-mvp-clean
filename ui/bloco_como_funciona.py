# BLOCO: COMO FUNCIONA (inserir onde está a área em branco após login)

import streamlit as st

def render_como_funciona():
    st.markdown(
        '''
        <div style="
            background:#ffffff;
            border:1px solid #e7e7e7;
            border-radius:14px;
            padding:20px 24px;
            margin-bottom:20px;
        ">
            <h3 style="margin-bottom:12px;">Como funciona</h3>

            <p><b>1. Marque no mapa a localização desejada</b><br>
            Clique no mapa para indicar o terreno ou ponto que você deseja analisar.</p>

            <p><b>2. Preencha os dados do lote</b><br>
            Informe testada, profundidade e, se necessário, marque as opções do terreno conforme o caso.</p>

            <p><b>3. Gere o estudo de viabilidade</b><br>
            Após definir a localização e preencher os dados, clique em <b>Gerar consulta aos índices urbanísticos</b> para visualizar os parâmetros urbanísticos e a análise inicial.</p>

            <p><b>4. Revise os resultados</b><br>
            O sistema apresentará a zona, os índices urbanísticos e a leitura preliminar de viabilidade do local escolhido.</p>

            <p><b>5. Gere o relatório completo, se desejar</b><br>
            Se quiser um material mais detalhado e organizado, clique para gerar o relatório completo com as informações da análise.</p>
        </div>
        ''',
        unsafe_allow_html=True
    )
