from __future__ import annotations

import streamlit as st

from .common import md, fmt_num


def render(ctx: dict) -> None:
    if ctx['ia_max'] is None or ctx['A_total'] is None:
        st.info("Sem Índice de Aproveitamento (IA) máximo cadastrado para esta zona/uso.")
    else:
        md(
            f"Além da ocupação no térreo, a zona também define o potencial construtivo total do lote por meio do **Índice de Aproveitamento (IA)**.\n\n"
            f"Se o **Índice de Aproveitamento (IA)** máximo da zona for **{fmt_num(ctx['ia_max'])}**, então o potencial construtivo total do lote será:\n\n"
            f"👉 **{fmt_num(ctx['A'])} m² × {fmt_num(ctx['ia_max'])} = {fmt_num(ctx['A_total'])} m²**\n\n"
            f"Esse é o total que pode ser distribuído entre térreo e pavimentos superiores, respeitando também os demais parâmetros urbanísticos."
        )
        if ctx['A_considerada'] is not None and ctx['A_ia_saldo'] is not None:
            md(
                f"Como o relatório adotou **{fmt_num(ctx['A_considerada'])} m²** no térreo, o saldo estimado para crescer acima fica assim:\n\n"
                f"👉 **{fmt_num(ctx['A_total'])} m² − {fmt_num(ctx['A_considerada'])} m² = {fmt_num(ctx['A_ia_saldo'])} m²**\n\n"
                f"**Saldo estimado para pavimentos superiores: {fmt_num(ctx['A_ia_saldo'])} m²**"
            )
            md(
                f"👉 **Leitura prática:** considerando a área adotada de **{fmt_num(ctx['A_considerada'])} m²** no térreo, ainda restam **{fmt_num(ctx['A_ia_saldo'])} m²** de potencial construtivo pelo **Índice de Aproveitamento (IA)** para crescimento em pavimentos superiores, desde que o projeto respeite também altura máxima, recuos, ventilação, iluminação, circulação e demais exigências aplicáveis."
            )
    if ctx['gabarito_m'] is not None:
        md(f"**Altura máxima da zona:** {fmt_num(ctx['gabarito_m'])} m")
        md(
            f"A altura máxima de **{fmt_num(ctx['gabarito_m'])} m** é um parâmetro geral da zona. Isso não significa autorização automática para uma residência unifamiliar atingir essa altura ou construir muitos pavimentos.\n\n"
            "No caso de uma residência unifamiliar, a altura real da edificação depende do projeto arquitetônico, da implantação no lote, da **Taxa de Ocupação (TO)**, da **Taxa de Permeabilidade (TP)**, dos recuos, do **Índice de Aproveitamento (IA)**, das normas técnicas aplicáveis e da confirmação no licenciamento municipal.\n\n"
            "👉 **Na prática:** para este estudo preliminar, a altura da zona serve como limite urbanístico geral, mas a quantidade real de pavimentos deve ser definida e aprovada no projeto."
        )
