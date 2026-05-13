from __future__ import annotations

import streamlit as st

from .common import md, fmt_num, fmt_pct


def render(ctx: dict) -> None:
    if ctx['tp_min'] is None or ctx['A_perm_min'] is None:
        st.info("Sem TP mínima cadastrada para esta zona/uso.")
        return
    md(
        f"A zona exige **{fmt_pct(ctx['tp_min'])}** de área permeável.\n\n"
        f"👉 **{fmt_num(ctx['A'])} m² × {fmt_pct(ctx['tp_min'])} = {fmt_num(ctx['A_perm_min'])} m²** obrigatórios permeáveis\n\n"
        "Isso quer dizer que parte do terreno precisa continuar permitindo a infiltração da água da chuva no solo."
    )
    if ctx['A_considerada'] is not None and ctx['A_livre'] is not None:
        md("**Área livre considerando a área adotada no relatório**")
        md(
            f"Como o relatório adotou **{fmt_num(ctx['A_considerada'])} m²** no térreo, a área livre remanescente no lote fica assim:\n\n"
            f"👉 **{fmt_num(ctx['A'])} m² − {fmt_num(ctx['A_considerada'])} m² = {fmt_num(ctx['A_livre'])} m²**"
        )
        md(f"**Área livre remanescente no lote: {fmt_num(ctx['A_livre'])} m²**")
        md(f"Desses, **{fmt_num(ctx['A_perm_min'])} m²** precisam permanecer permeáveis.")
        if ctx['A_impermeavel_possivel'] is not None:
            md(
                f"Assim, restam:\n\n👉 **{fmt_num(ctx['A_livre'])} m² − {fmt_num(ctx['A_perm_min'])} m² = {fmt_num(ctx['A_impermeavel_possivel'])} m²**\n\n"
                f"**Área que ainda pode receber piso impermeável: {fmt_num(ctx['A_impermeavel_possivel'])} m²**"
            )
        leitura_tp = (
            f"como a área pretendida inicial de **{fmt_num(ctx['area_pedida'])} m²** excedeu o limite adotado no relatório, os cálculos passaram a considerar **{fmt_num(ctx['A_considerada'])} m²** no térreo"
            if ctx['excedeu_area'] and ctx['area_pedida'] is not None
            else f"os cálculos passaram a considerar a própria área pretendida informada, de **{fmt_num(ctx['A_considerada'])} m²** no térreo"
        )
        md(
            f"👉 **Leitura prática:** {leitura_tp}. Com isso, a área livre remanescente fica em **{fmt_num(ctx['A_livre'])} m²**, "
            f"dos quais **{fmt_num(ctx['A_perm_min'])} m²** devem permanecer permeáveis para atender à exigência mínima da zona."
        )
    else:
        md("**Ver cenários usando os limites de referência**")
        if ctx['tp2'] is not None and ctx['A_op2_max'] is not None:
            a_rest, a_imperm = ctx['tp2']
            md("✅ **Cenário A — leitura com flexibilidade do Art. 112**")
            md(
                f"Se você utilizar **{fmt_num(ctx['A_op2_max'])} m²** no térreo:\n\n"
                f"👉 Área restante no lote: **{fmt_num(ctx['A'])} m² − {fmt_num(ctx['A_op2_max'])} m² = {fmt_num(a_rest)} m²**\n\n"
                f"Desses:\n\n"
                f"- **{fmt_num(ctx['A_perm_min'])} m²** devem permitir infiltração no solo\n"
                f"- **{fmt_num(a_imperm)} m²** podem receber piso impermeável"
            )
        if ctx['tp1'] is not None and ctx['A_op1_max'] is not None:
            a_rest, a_imperm = ctx['tp1']
            md("✅ **Cenário B — leitura com recuos padrão da zona**")
            md(
                f"Se você utilizar **{fmt_num(ctx['A_op1_max'])} m²** no térreo:\n\n"
                f"👉 Área restante no lote: **{fmt_num(ctx['A'])} m² − {fmt_num(ctx['A_op1_max'])} m² = {fmt_num(a_rest)} m²**\n\n"
                f"Desses:\n\n"
                f"- **{fmt_num(ctx['A_perm_min'])} m²** devem permitir infiltração no solo\n"
                f"- **{fmt_num(a_imperm)} m²** podem receber piso impermeável"
            )
        md(
            "**Leitura prática:** nas duas opções, o lote precisa manter a área permeável mínima. "
            "A diferença está em quanto sobra livre além desse mínimo."
        )
