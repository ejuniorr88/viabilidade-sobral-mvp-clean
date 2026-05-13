from __future__ import annotations

from .common import md


_FECHAMENTO_FINAL = (
    "Este relatório é uma análise inicial para ajudar a entender o potencial urbanístico do terreno.\n\n"
    "Ele não representa aprovação automática da Prefeitura e não substitui alvará, licença, certidão, "
    "parecer técnico ou análise oficial do órgão competente.\n\n"
    "Antes de construir, reformar, regularizar, parcelar ou protocolar um projeto, é necessário confirmar "
    "as informações do lote, a documentação do imóvel, as regras da zona, as condições da via e as "
    "exigências do licenciamento municipal.\n\n"
    "A decisão final sobre a aprovação do projeto cabe sempre ao órgão público responsável."
)


def render(ctx: dict) -> None:
    # Mantém as frases históricas protegidas por contrato e deixa o fechamento
    # mais claro para o usuário leigo, sem alterar cálculo ou adequabilidade.
    md(
        "Este relatório foi pensado para ajudar a entender o terreno de forma mais simples.\n\n"
        "Na etapa de projeto e aprovação, ainda será preciso conferir os detalhes completos no setor de licenciamento de obras da prefeitura.\n\n"
        f"{_FECHAMENTO_FINAL}"
    )
