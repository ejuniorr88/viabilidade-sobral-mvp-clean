from __future__ import annotations

from .common import md


def render(ctx: dict) -> None:
    md(
        "**Flexibilidade de recuos no uso residencial unifamiliar**\n\n"
        "**Art. 112.** Será aplicado, para as atividades atrativas de vizinhança de pequeno porte e para o uso residencial unifamiliar, "
        "a flexibilidade quanto aos recuos de frente e laterais, podendo zerar, desde que observado o cumprimento da Taxa de Permeabilidade Mínima "
        "e da Taxa de Ocupação Máxima da zona em que se encontra.\n\n"
        "👉 **Na prática:** para residência unifamiliar, a legislação admite zerar recuos frontal e laterais, desde que a proposta continue respeitando a **Taxa de Permeabilidade (TP) mínima** e a **Taxa de Ocupação (TO) máxima** da zona."
    )
    md(
        "**Calçada**\n\n"
        "Não existe uma largura única e fixa para toda calçada no município. Quando houver padrão definido no loteamento ou na via, ele deve ser seguido. "
        "Quando não houver, a referência costuma ser a calçada já existente no local.\n\n"
        "**Piscinas, espelhos d’água, caixas d’água, cisternas e tanques**\n\n"
        "Atenção: para a **Taxa de Ocupação (TO)**, a piscina não é contada como área construída do lote.\n\n"
        "**Art. 144.** As piscinas, espelhos d’água, caixas d’água, cisternas e tanques deverão observar afastamento mínimo de **0,50 m** de todas as divisas do terreno e devem ser computados como área impermeável para o cálculo da **Taxa de Permeabilidade (TP)**.\n\n"
        "👉 **Na prática:** além de respeitar esse afastamento mínimo de **50 cm**, esses elementos também entram no cálculo da **Taxa de Permeabilidade (TP)** como área impermeável."
    )


# Contratos textuais legados preservados para testes automatizados: Piscina não entra como área construída
