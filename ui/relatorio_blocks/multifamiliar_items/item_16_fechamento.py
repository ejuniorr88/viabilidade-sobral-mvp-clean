from __future__ import annotations
from . import common


def render(ctx):
    common.st.markdown(
        "Este relatório foi pensado para ajudar a entender o terreno de forma mais simples.\n\n"
        "Na etapa de projeto e aprovação, ainda será preciso conferir os detalhes completos no setor de licenciamento de obras da prefeitura."
    )
