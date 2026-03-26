from __future__ import annotations

from .common import md


def render(ctx: dict) -> None:
    md(
        "Este relatório foi pensado para ajudar a entender o terreno de forma mais simples.\n\n"
        "Na etapa de projeto e aprovação, ainda será preciso conferir os detalhes completos no licenciamento."
    )
