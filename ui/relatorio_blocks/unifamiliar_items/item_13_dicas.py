from __future__ import annotations

from .common import md


def render(ctx: dict) -> None:
    md(
        "**Flexibilidade de recuos no uso residencial unifamiliar**\n\n"
        "**Art. 112.** Será aplicado, para as atividades atrativas de vizinhança de pequeno porte e para o uso residencial unifamiliar, "
        "a flexibilidade quanto aos recuos de frente e laterais, podendo zerar, desde que observado o cumprimento da Taxa de Permeabilidade Mínima "
        "e da Taxa de Ocupação Máxima da zona em que se encontra.\n\n"
        "👉 **Na prática:** para residência unifamiliar, a legislação admite zerar recuos frontal e laterais, desde que a proposta continue respeitando a **TP mínima** e a **TO máxima** da zona."
    )
    md(
        "**Calçada**\n\n"
        "Não existe uma largura única e fixa para toda calçada no município. Quando houver padrão definido no loteamento ou na via, ele deve ser seguido. "
        "Quando não houver, a referência costuma ser a calçada já existente no local.\n\n"
        "**Piscina**\n\n"
        "Piscina não entra como área construída para a Taxa de Ocupação (TO). Mas ela conta como área impermeável para a Taxa de Permeabilidade (TP). "
        "Além disso, deve respeitar afastamento mínimo de 0,50 m das divisas."
    )
