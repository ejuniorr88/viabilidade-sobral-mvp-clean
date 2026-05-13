from __future__ import annotations
from . import common


def render(ctx):
    # Mantém as frases históricas protegidas por contrato e acrescenta a
    # blindagem jurídica geral solicitada para a fase de zoneamentos.
    common.st.markdown(
        "Este relatório foi pensado para ajudar a entender o terreno de forma mais simples.\n\n"
        "Na etapa de projeto e aprovação, ainda será preciso conferir os detalhes completos no setor de licenciamento de obras da prefeitura.\n\n"
        "**Aviso importante:** este relatório é uma análise urbanística preliminar, privada e informativa. "
        "Ele não substitui consulta, parecer, certidão, alvará, licença, manifestação oficial da Prefeitura ou decisão de órgão competente. "
        "Antes de protocolar, construir, reformar, parcelar ou executar qualquer intervenção, confirme a legislação aplicável, a documentação do imóvel, "
        "as condições do lote, a tipologia escolhida e as exigências específicas no licenciamento municipal."
    )
