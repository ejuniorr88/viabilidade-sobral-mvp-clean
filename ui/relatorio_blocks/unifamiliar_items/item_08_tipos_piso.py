from __future__ import annotations

from .common import md, md_table


def render(ctx: dict) -> None:
    md("Nem todo piso externo conta do mesmo jeito na permeabilidade. Veja como a lei trata isso:")
    md(
        md_table(
            [
                ("Grama", "100%"),
                ("Brita solta / terra batida", "100%"),
                ("Piso drenante", "90%"),
                ("Bloco de concreto vazado (“piso verde”)", "60%"),
                ("Pedra portuguesa / intertravado", "25%"),
            ]
        )
    )
    md("Isso ajuda a entender que nem toda área “livre” do lote conta 100% como permeável.")
