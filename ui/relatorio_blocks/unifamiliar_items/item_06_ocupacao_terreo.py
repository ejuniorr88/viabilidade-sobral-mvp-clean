from __future__ import annotations

import streamlit as st

from .common import md, fmt_num, fmt_pct


def render(ctx: dict) -> None:
    if ctx['to_max'] is None or ctx['A_to'] is None:
        st.info("Sem TO máxima cadastrada para esta zona/uso.")
        return

    md(
        f"A zona permite ocupar até **{fmt_pct(ctx['to_max'])}** do terreno no térreo.\n\n"
        f"👉 **{fmt_num(ctx['A'])} m² × {fmt_pct(ctx['to_max'])} = {fmt_num(ctx['A_to'])} m²**\n\n"
        "Esse é o limite máximo permitido pela **Taxa de Ocupação (TO)**."
    )

    if ctx.get('A_considerada') is not None and ctx.get('area_pedida') is not None:
        md(
            f"Como foi informada uma **Área Construída Pretendida** de **{fmt_num(ctx['area_pedida'])} m²**, "
            "o item passa a comparar esse valor com os limites aplicáveis ao terreno."
        )
        if ctx.get('excedeu_area'):
            md(
                f"👉 **Área pretendida informada:** **{fmt_num(ctx['area_pedida'])} m²**\n\n"
                f"👉 **Área adotada no relatório:** **{fmt_num(ctx['A_considerada'])} m²**\n\n"
                "Como a área informada ultrapassou o limite adotado para o estudo, os cálculos abaixo passam a considerar o valor máximo permitido pelo terreno."
            )
        else:
            md(
                f"👉 **Área pretendida informada:** **{fmt_num(ctx['area_pedida'])} m²**\n\n"
                f"👉 **Área adotada no relatório:** **{fmt_num(ctx['A_considerada'])} m²**"
            )

        if ctx.get('to_projeto_pct') is not None:
            md(
                f"Isso representa uma **TO efetiva de {fmt_pct(ctx['to_projeto_pct'])}**, considerando a área adotada no relatório."
            )

        if ctx.get('A_op2_max') is not None:
            situacao_op2 = "cabe" if ctx['A_considerada'] <= ctx['A_op2_max'] else "não cabe"
            md(
                f"✅ **Comparação com a Opção principal (Art. 112):** a área adotada de **{fmt_num(ctx['A_considerada'])} m²** {situacao_op2} "
                f"dentro do limite de **{fmt_num(ctx['A_op2_max'])} m²** nesta leitura."
            )

        if ctx.get('A_recuos') is not None:
            situacao_recuos = "cabe" if ctx['A_considerada'] <= ctx['A_recuos'] else "não cabe"
            md(
                f"✅ **Comparação com os recuos da zona:** a área adotada de **{fmt_num(ctx['A_considerada'])} m²** {situacao_recuos} "
                f"dentro do limite físico de **{fmt_num(ctx['A_recuos'])} m²** quando todos os recuos são respeitados."
            )

        md(
            f"**Leitura prática:** para o estudo deste lote, o relatório passa a considerar **{fmt_num(ctx['A_considerada'])} m²** no térreo, "
            "sempre limitado pela TO máxima e pelas demais exigências urbanísticas aplicáveis."
        )
        return

    md(
        "Mas aqui tem um ponto importante: uma coisa é o limite da zona no papel, e outra é o que realmente cabe dentro do lote depois de respeitar os recuos.\n\n"
        "Por isso, além do percentual permitido, também vale olhar a área que sobra de forma prática dentro do terreno."
    )
    md(
        "> **Art. 112.** Será aplicado, para as atividades atrativas de vizinhança de pequeno porte e para o uso residencial unifamiliar, "
        "a flexibilidade quanto aos recuos de frente e laterais, podendo zerar, desde que observado o cumprimento da Taxa de Permeabilidade Mínima "
        "e da Taxa de Ocupação Máxima da zona em que se encontra."
    )
    md(
        "👉 **Na prática:** para residência unifamiliar, a norma permite encostar nas laterais e alinhar na frente, desde que o projeto continue respeitando a **TO máxima** e a **TP mínima**."
    )
    md("Agora veja duas possibilidades de leitura:")
    md("✅ **Opção principal — aproveitando a flexibilidade da lei**")
    md(
        "Para este caso, a legislação admite **zerar recuo frontal e laterais**.\n\n"
        "Assim, o térreo pode aproveitar melhor a área do lote, desde que continue respeitando TO e TP.\n\n"
        f"👉 **Térreo máximo nesta opção:** **{fmt_num(ctx['A_to'])} m²**\n\n"
        "⚠️ O recuo de fundo e as demais exigências aplicáveis continuam precisando ser respeitados."
    )
    if ctx['A_recuos'] is not None:
        md("✅ **Opção alternativa — adotando os recuos da zona**")
        md(f"- **Frontal:** {fmt_num(ctx['rec_fr'])} m")
        md(f"- **Laterais:** {fmt_num(ctx['rec_lat'])} m cada")
        md(f"- **Fundo:** {fmt_num(ctx['rec_fun'])} m")
        md(f"- **Largura útil:** {fmt_num(ctx['W_util'])} m")
        md(f"- **Profundidade útil:** {fmt_num(ctx['D_util'])} m")
        md(f"👉 **{fmt_num(ctx['W_util'])} × {fmt_num(ctx['D_util'])} = {fmt_num(ctx['A_recuos'])} m²**")
        md(
            f"👉 Neste cenário, mesmo que a zona permita até **{fmt_num(ctx['A_to'])} m²**, o limite físico pelos recuos fica em **{fmt_num(ctx['A_recuos'])} m²**."
        )
        md(
            f"**Leitura prática:** pela TO, o lote pode ocupar até **{fmt_num(ctx['A_to'])} m²** no térreo. Mas, se você optar por seguir os recuos da zona, a implantação prática cai para **{fmt_num(ctx['A_recuos'])} m²**."
        )
