from __future__ import annotations

from .common import md, md_table


def render(ctx: dict) -> None:
    md("Nem todo piso externo conta do mesmo jeito na permeabilidade. Veja como a lei trata isso:")

    headers = [
        "Tipo de Piso",
        "Percentual considerado permeável",
    ]

    rows = [
        ["Grama", "100%"],
        ["Brita solta / terra batida", "100%"],
        ["Piso drenante", "90%"],
        ['Bloco de concreto vazado (“piso verde”)', "60%"],
        ["Pedra portuguesa / intertravado", "25%"],
    ]

    md_table(headers, rows)

    md("Isso ajuda a entender que nem toda área sem ocupação no térreo conta 100% como área permeável.")
