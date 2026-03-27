from __future__ import annotations

import streamlit as st

from .common import md, fmt_num, fmt_pct


def render(ctx: dict) -> None:
    if ctx["to_max"] is None or ctx["A_to"] is None:
        st.info("Sem TO máxima cadastrada para esta zona/uso.")
        return

    md(
        f"A zona permite ocupar até **{fmt_pct(ctx['to_max'])}** do terreno no térreo.\n\n"
        f"👉 **{fmt_num(ctx['A'])} m² × {fmt_pct(ctx['to_max'])} = {fmt_num(ctx['A_to'])} m²**\n\n"
        "Esse é o limite máximo permitido pela **Taxa de Ocupação (TO)**.\n\n"
        f"Na prática, isso significa que a edificação não pode ultrapassar **{fmt_num(ctx['A_to'])} m²** no chão, considerando a ocupação máxima permitida pela zona."
    )

    if ctx.get('area_pedida') is not None and ctx.get('A_considerada') is not None:
        if ctx.get('excedeu_area'):
            md(
                f"👉 **Área pretendida informada:** **{fmt_num(ctx['area_pedida'])} m²**. "
                f"Como esse valor ultrapassa o limite adotado no relatório, os cálculos abaixo passam a considerar **{fmt_num(ctx['A_considerada'])} m²** no térreo."
            )
        else:
            md(
                f"👉 **Área pretendida informada:** **{fmt_num(ctx['area_pedida'])} m²**. "
                f"Como esse valor cabe dentro dos limites urbanísticos do lote, os cálculos abaixo passam a considerar essa mesma área no térreo."
            )

    md("**Opção 1 — usando os recuos da zona**")
    md("No caso de usar todos os recuos conforme a zona, a área útil de implantação fica assim:")

    if ctx['W_util'] is not None:
        md("**1. Cálculo da largura útil**")
        md(f"A largura original do lote é de **{fmt_num(ctx['W'])} m**.")
        md("Como a zona exige:")
        md(f"**{fmt_num(ctx['rec_lat'])} m** de recuo lateral de um lado")
        md(f"**{fmt_num(ctx['rec_lat'])} m** de recuo lateral do outro lado")
        md("fazemos:")
        md(f"👉 **{fmt_num(ctx['W'])} − {fmt_num(ctx['rec_lat'])} − {fmt_num(ctx['rec_lat'])} = {fmt_num(ctx['W_util'])}**")
        md(f"**Largura útil:** {fmt_num(ctx['W_util'])} m")

    if ctx['D_util'] is not None:
        md("**2. Cálculo da profundidade útil**")
        md(f"A profundidade original do lote é de **{fmt_num(ctx['D'])} m**.")
        md("Como a zona exige:")
        md(f"**{fmt_num(ctx['rec_fr'])} m** de recuo frontal")
        md(f"**{fmt_num(ctx['rec_fun'])} m** de recuo de fundo")
        md("fazemos:")
        md(f"👉 **{fmt_num(ctx['D'])} − {fmt_num(ctx['rec_fr'])} − {fmt_num(ctx['rec_fun'])} = {fmt_num(ctx['D_util'])}**")
        md(f"**Profundidade útil:** {fmt_num(ctx['D_util'])} m")

    if ctx['A_recuos'] is not None:
        md("**3. Cálculo da área útil de implantação**")
        md(f"👉 **{fmt_num(ctx['W_util'])} × {fmt_num(ctx['D_util'])} = {fmt_num(ctx['A_recuos'])}**")
        md(
            f"**Leitura prática:** isso significa que, mesmo que a zona permita ocupar até **{fmt_num(ctx['A_to'])} m²** pela TO, ao aplicar todos os recuos da zona o espaço que realmente sobra para implantar a edificação no térreo fica em **{fmt_num(ctx['A_recuos'])} m²**."
        )

    md("**Opção 2 — no caso do R2.1**")
    md(
        "Quando a zona admitir leitura semelhante ao unifamiliar, o projeto pode adotar essa lógica de implantação.\n\n"
        f"👉 Nesse caso, o aproveitamento do térreo pode chegar ao limite máximo de **{fmt_num(ctx['A_to'])} m²** pela Taxa de Ocupação (TO), desde que também sejam respeitadas as demais exigências urbanísticas aplicáveis ao caso."
    )

    md("**Leitura final**")
    leitura_recuos = (
        f"Quando são aplicados integralmente os recuos da zona, a área útil de implantação fica em **{fmt_num(ctx['A_recuos'])} m²**. "
        if ctx['A_recuos'] is not None
        else ""
    )
    leitura_area = ""
    if ctx.get('area_pedida') is not None and ctx.get('A_considerada') is not None:
        if ctx.get('excedeu_area'):
            leitura_area = (
                f"Como a área pretendida informada foi de **{fmt_num(ctx['area_pedida'])} m²**, mas o relatório precisou adotar **{fmt_num(ctx['A_considerada'])} m²** para respeitar os limites urbanísticos do lote, essa é a área considerada nesta leitura. "
            )
        else:
            leitura_area = (
                f"Como a área pretendida informada foi de **{fmt_num(ctx['area_pedida'])} m²** e cabe dentro dos limites urbanísticos do lote, essa própria área foi considerada nesta leitura. "
            )
    md(
        f"A Taxa de Ocupação (TO) permite ocupar até **{fmt_num(ctx['A_to'])} m²** no térreo. {leitura_recuos}Já no caso do R2.1, quando a zona admitir leitura semelhante ao unifamiliar, o aproveitamento do térreo pode chegar ao limite máximo de **{fmt_num(ctx['A_to'])} m²** pela TO, desde que também sejam respeitadas as demais exigências urbanísticas aplicáveis ao caso, como adequabilidade, permeabilidade e demais parâmetros da zona. {leitura_area}"
    )
