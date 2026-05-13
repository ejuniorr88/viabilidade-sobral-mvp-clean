from __future__ import annotations

import streamlit as st

from .common import md, fmt_num
from ui.relatorio_blocks.terreno_irregular import aviso_texto, limite_to_text


def _fmt_pct_local(v) -> str:
    try:
        return f"{float(v):.1f}%".replace(".", ",")
    except Exception:
        return "—"


def render(ctx: dict) -> None:
    if ctx.get("to_max") is None or ctx.get("A_to") is None:
        st.info("Sem TO máxima cadastrada para esta zona/uso.")
        return

    area_lote = ctx.get("A")
    to_max = ctx.get("to_max")
    area_to = ctx.get("A_to")
    area_pedida = ctx.get("area_pedida")
    area_considerada = ctx.get("A_considerada")
    excedeu_area = bool(ctx.get("excedeu_area"))

    rec_fr = ctx.get("rec_fr")
    rec_lat = ctx.get("rec_lat")
    rec_fun = ctx.get("rec_fun")
    w_util = ctx.get("W_util")
    d_util = ctx.get("D_util")
    a_recuos = ctx.get("A_recuos")

    pct_txt = _fmt_pct_local(to_max)

    md(
        f"""A zona permite ocupar até **{pct_txt}** do terreno no térreo.\n\n"""
        f"""👉 **{fmt_num(area_lote)} m² × {pct_txt} = {fmt_num(area_to)} m²**\n\n"""
        """Esse é o limite máximo permitido pela Taxa de Ocupação (TO)."""
    )

    to_efetiva = None
    if area_pedida is not None and area_lote:
        try:
            to_efetiva = (float(area_pedida) / float(area_lote)) * 100.0
        except Exception:
            to_efetiva = None

    if area_pedida is not None and area_considerada is not None:
        if excedeu_area:
            md(
                f"""👉 **Área pretendida informada: {fmt_num(area_pedida)} m².** Como esse valor ultrapassa o limite máximo permitido pela TO, ele não pode ser adotado como referência de implantação no térreo. Por isso, o estudo passa a considerar **{fmt_num(area_considerada)} m²** como teto urbanístico inicial para esta análise."""
            )
            if to_efetiva is not None:
                md(
                    f"""👉 **TO correspondente à área pretendida: {fmt_num(area_pedida)} m² ÷ {fmt_num(area_lote)} m² = {_fmt_pct_local(to_efetiva)}**\n\n"""
                    f"""Isso significa que, para esta proposta, a ocupação no térreo ficaria em **{_fmt_pct_local(to_efetiva)}** do lote, portanto acima da TO máxima permitida de **{pct_txt}**."""
                )
        else:
            md(
                f"""👉 **Área pretendida informada: {fmt_num(area_pedida)} m².** Como esse valor está abaixo do limite máximo permitido, ele pode ser adotado como referência inicial para a implantação no térreo."""
            )
            if to_efetiva is not None:
                md(
                    f"""👉 **TO correspondente à área pretendida: {fmt_num(area_pedida)} m² ÷ {fmt_num(area_lote)} m² = {_fmt_pct_local(to_efetiva)}**\n\n"""
                    f"""Isso significa que, para esta proposta, a ocupação no térreo ficaria em **{_fmt_pct_local(to_efetiva)}** do lote, portanto abaixo da TO máxima permitida de **{pct_txt}**."""
                )

    if ctx.get("is_irregular"):
        md("**Terreno irregular — leitura pela área total**")
        md(aviso_texto())
        md(limite_to_text(fmt_num(area_to)))
        if area_pedida is not None and area_considerada is not None:
            if excedeu_area:
                md(f"👉 **Neste caso, a área pretendida precisa ser reduzida para respeitar o limite máximo de {fmt_num(area_considerada)} m² pela Taxa de Ocupação.**")
            else:
                md(f"👉 **Neste caso, a área pretendida de {fmt_num(area_pedida)} m² está dentro do limite máximo pela Taxa de Ocupação.**")
        else:
            md("👉 **Sem área pretendida informada, o estudo apresenta o limite máximo pela Taxa de Ocupação como referência inicial.**")
        return

    md(
        """Como complemento a essa verificação, também é importante analisar a área que efetivamente cabe no lote, considerando os recuos aplicáveis.\n\n"""
        """Art. 112. Será aplicado, para as atividades atrativas de vizinhança de pequeno porte e para o uso residencial unifamiliar, a flexibilidade quanto aos recuos de frente e laterais, podendo zerar, desde que observado o cumprimento da Taxa de Permeabilidade Mínima e da Taxa de Ocupação Máxima da zona em que se encontra.\n\n"""
        """👉 **Na prática:** para residência unifamiliar, a norma permite encostar nas laterais e alinhar na frente, desde que o projeto continue respeitando a TO máxima e a TP mínima.\n\n"""
        """A partir disso, este lote pode ser lido de duas formas:"""
    )

    md(
        f"""✅ **Cenário A — leitura com flexibilidade do Art. 112**\n\n"""
        """Para este caso, a legislação admite zerar o recuo frontal e os recuos laterais.\n\n"""
        """Assim, o térreo pode aproveitar melhor a área do lote, desde que continue respeitando a TO e a TP.\n\n"""
        f"""👉 **Térreo máximo neste cenário: {fmt_num(area_to)} m²**"""
    )

    if area_pedida is not None and area_considerada is not None:
        if excedeu_area:
            md(
                f"""👉 **Como a área pretendida informada foi de {fmt_num(area_pedida)} m², ela não é permitida nesta leitura, porque ultrapassa a Taxa de Ocupação máxima da zona. Portanto, para esta hipótese, o estudo passa a considerar {fmt_num(area_considerada)} m² como limite máximo admissível no térreo.**"""
            )
        else:
            md(
                f"""👉 **Como a área pretendida informada foi de {fmt_num(area_pedida)} m², ela cabe dentro desse limite máximo.**"""
            )

    md("""⚠️ **O recuo de fundo e as demais exigências urbanísticas aplicáveis continuam precisando ser respeitados.**""")

    md("""✅ **Cenário B — leitura com recuos padrão da zona**\n\nCaso se opte por seguir os recuos padrão da zona, a implantação prática fica assim:""")

    if rec_fr is not None:
        md(f"""Frontal: **{fmt_num(rec_fr)} m**""")
    if rec_lat is not None:
        md(f"""Laterais: **{fmt_num(rec_lat)} m cada**""")
    if rec_fun is not None:
        md(f"""Fundo: **{fmt_num(rec_fun)} m**""")

    md("""Com isso, a área útil de implantação no térreo passa a ser:""")

    if w_util is not None:
        md(f"""Largura útil: **{fmt_num(w_util)} m**""")
    if d_util is not None:
        md(f"""Profundidade útil: **{fmt_num(d_util)} m**""")

    if a_recuos is not None and w_util is not None and d_util is not None:
        md(
            f"""👉 **{fmt_num(w_util)} × {fmt_num(d_util)} = {fmt_num(a_recuos)} m²**\n\n"""
            f"""👉 Nesse cenário, mesmo que a zona permita até **{fmt_num(area_to)} m²** pela TO, o limite físico de implantação, considerando os recuos, fica em **{fmt_num(a_recuos)} m²**."""
        )

        if area_pedida is not None and area_considerada is not None:
            if excedeu_area:
                if area_pedida <= a_recuos:
                    md(
                        f"""👉 **Como a área pretendida informada foi de {fmt_num(area_pedida)} m², ela cabe fisicamente pelos recuos, mas não pode ser adotada porque ultrapassa a Taxa de Ocupação máxima da zona. Portanto, o limite real continua sendo {fmt_num(area_considerada)} m² no térreo.**"""
                    )
                else:
                    md(
                        f"""👉 **Como a área pretendida informada foi de {fmt_num(area_pedida)} m², ela ultrapassa a TO máxima e também não cabe fisicamente dentro da área disponível pelos recuos. Portanto, o limite real continua sendo {fmt_num(area_considerada)} m² no térreo.**"""
                    )
            else:
                md(
                    f"""👉 **Como a área pretendida informada foi de {fmt_num(area_pedida)} m², ela também cabe dentro desse limite físico.**"""
                )

    md("""**Leitura prática**""")

    md(f"""Pela Taxa de Ocupação (TO), o lote pode ocupar até **{fmt_num(area_to)} m²** no térreo.""")

    if area_pedida is not None and area_considerada is not None:
        if not excedeu_area and to_efetiva is not None:
            md(
                f"""A área pretendida informada foi de **{fmt_num(area_pedida)} m²**, o que corresponde a uma TO efetiva de **{_fmt_pct_local(to_efetiva)}**."""
            )

        if excedeu_area:
            md(
                f"""Isso significa que uma proposta com **{fmt_num(area_pedida)} m²** no térreo não é urbanisticamente possível, porque excede o limite máximo permitido pela zona."""
            )
            md(
                f"""Na leitura com a flexibilidade do art. 112, o teto máximo admissível passa a ser **{fmt_num(area_considerada)} m²**."""
            )
            if a_recuos is not None:
                md(
                    f"""Na leitura com os recuos padrão da zona, a construção até caberia fisicamente em **{fmt_num(a_recuos)} m²**, mas esse valor não autoriza ocupar acima da TO."""
                )
                md(
                    f"""👉 **Neste caso, a área pretendida de {fmt_num(area_pedida)} m² não pode ser considerada viável, porque ultrapassa a TO máxima permitida. Na prática, o projeto precisaria ser reduzido para respeitar no máximo {fmt_num(area_considerada)} m² no térreo.**"""
                )
            else:
                md(
                    f"""👉 **Neste caso, a área pretendida de {fmt_num(area_pedida)} m² não pode ser considerada viável, porque ultrapassa a TO máxima permitida. Na prática, o projeto precisaria ser reduzido para se enquadrar nos parâmetros urbanísticos, respeitando no máximo {fmt_num(area_considerada)} m² pela TO.**"""
                )
        else:
            md(f"""Na leitura com a flexibilidade do art. 112, a área pretendida de **{fmt_num(area_pedida)} m²** é viável.""")
            if a_recuos is not None:
                md(f"""Na leitura com os recuos padrão da zona, a área útil de implantação cai para **{fmt_num(a_recuos)} m²**, mas a área pretendida de **{fmt_num(area_pedida)} m²** continua sendo viável.""")
                md("""👉 **Neste caso, a área pretendida informada permanece viável nas duas leituras: tanto pela TO máxima da zona quanto pela implantação prática com recuos.**""")
            else:
                md("""👉 **Neste caso, a área pretendida informada permanece viável pela TO máxima da zona.**""")
    else:
        md("""Na leitura com a flexibilidade do art. 112, o aproveitamento do térreo pode chegar ao limite máximo permitido pela zona, desde que sejam respeitadas a TO, a TP e as demais exigências aplicáveis.""")
        if a_recuos is not None:
            md(f"""Na leitura com os recuos padrão da zona, a construção até caberia fisicamente em **{fmt_num(a_recuos)} m²**, mas esse valor não autoriza ocupar acima da TO.""")
            md(f"""👉 **Neste caso, sem uma área pretendida informada, o estudo usa como referência o limite real de ocupação no térreo: {fmt_num(area_to)} m² pela TO.**""")
        else:
            md("""👉 **Neste caso, sem uma área pretendida informada, o estudo passa a apresentar o limite máximo pela TO como referencial principal do lote.**""")
