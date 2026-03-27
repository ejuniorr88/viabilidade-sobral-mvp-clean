from __future__ import annotations

import streamlit as st

from .common import md, fmt_num


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

    w = ctx.get("W")
    d = ctx.get("D")
    rec_fr = ctx.get("rec_fr")
    rec_lat = ctx.get("rec_lat")
    rec_fun = ctx.get("rec_fun")
    w_util = ctx.get("W_util")
    d_util = ctx.get("D_util")
    a_recuos = ctx.get("A_recuos")

    pct_txt = _fmt_pct_local(to_max)

    md(
        f"""A zona permite ocupar até **{pct_txt}** do terreno no térreo.

"""
        f"""👉 **{fmt_num(area_lote)} m² × {pct_txt} = {fmt_num(area_to)} m²**

"""
        """Esse é o limite máximo permitido pela Taxa de Ocupação (TO)."""
    )

    if area_pedida is not None and area_considerada is not None:
        if excedeu_area:
            md(
                f"""👉 **Área pretendida informada: {fmt_num(area_pedida)} m².** Como esse valor ultrapassa o limite máximo permitido, o estudo passa a considerar **{fmt_num(area_considerada)} m²** como referência inicial para a implantação no térreo."""
            )
        else:
            md(
                f"""👉 **Área pretendida informada: {fmt_num(area_pedida)} m².** Como esse valor está abaixo do limite máximo permitido, ele pode ser adotado como referência inicial para a implantação no térreo."""
            )

    md(
        """Como complemento a essa verificação, também é importante analisar a área que efetivamente cabe no lote, considerando os recuos aplicáveis.

"""
        """Art. 112. Será aplicado, para as atividades atrativas de vizinhança de pequeno porte e para o uso residencial unifamiliar, a flexibilidade quanto aos recuos de frente e laterais, podendo zerar, desde que observado o cumprimento da Taxa de Permeabilidade Mínima e da Taxa de Ocupação Máxima da zona em que se encontra.

"""
        """👉 **Na prática:** para residência unifamiliar, a norma permite encostar nas laterais e alinhar na frente, desde que o projeto continue respeitando a TO máxima e a TP mínima.

"""
        """A partir disso, este lote pode ser lido de duas formas:"""
    )

    md(
        f"""✅ **Opção principal — aproveitando a flexibilidade da lei**

"""
        """Para este caso, a legislação admite zerar o recuo frontal e os recuos laterais.

"""
        """Assim, o térreo pode aproveitar melhor a área do lote, desde que continue respeitando a TO e a TP.

"""
        f"""👉 **Térreo máximo nesta opção: {fmt_num(area_to)} m²**"""
    )

    if area_pedida is not None and area_considerada is not None:
        ref_area = area_considerada if excedeu_area else area_pedida
        md(
            f"""👉 **Como a área pretendida informada foi de {fmt_num(area_pedida)} m², ela cabe dentro desse limite máximo.**"""
            if not excedeu_area
            else f"""👉 **Como a área pretendida informada foi de {fmt_num(area_pedida)} m², ela ultrapassa esse limite máximo. Para esta leitura, passa a ser considerada a área de {fmt_num(ref_area)} m².**"""
        )

    md("""⚠️ **O recuo de fundo e as demais exigências urbanísticas aplicáveis continuam precisando ser respeitados.**""")

    md("""✅ **Opção alternativa — adotando os recuos da zona**

Caso se opte por seguir os recuos padrão da zona, a implantação prática fica assim:""")

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
            f"""👉 **{fmt_num(w_util)} × {fmt_num(d_util)} = {fmt_num(a_recuos)} m²**

"""
            f"""👉 Nesse cenário, mesmo que a zona permita até **{fmt_num(area_to)} m²** pela TO, o limite físico de implantação, considerando os recuos, fica em **{fmt_num(a_recuos)} m²**."""
        )

        if area_pedida is not None and area_considerada is not None:
            ref_area = area_considerada if excedeu_area else area_pedida
            md(
                f"""👉 **Como a área pretendida informada foi de {fmt_num(area_pedida)} m², ela também cabe dentro desse limite físico.**"""
                if ref_area <= a_recuos
                else f"""👉 **Como a área pretendida informada foi de {fmt_num(area_pedida)} m², ela não cabe dentro desse limite físico. Para esta leitura, passa a ser considerada a área de {fmt_num(a_recuos)} m² como teto de implantação com recuos.**"""
            )

    md("""**Leitura prática**""")

    md(f"""Pela Taxa de Ocupação (TO), o lote pode ocupar até **{fmt_num(area_to)} m²** no térreo.""")

    if area_pedida is not None and area_considerada is not None:
        ref_area = area_considerada if excedeu_area else area_pedida

        if not excedeu_area:
            md(f"""Na leitura com a flexibilidade do art. 112, a área pretendida de **{fmt_num(area_pedida)} m²** é viável.""")
        else:
            md(f"""Na leitura com a flexibilidade do art. 112, a área pretendida de **{fmt_num(area_pedida)} m²** ultrapassa o limite máximo, por isso a leitura passa a considerar **{fmt_num(ref_area)} m²** como teto pela TO.""")

        if a_recuos is not None:
            if ref_area <= a_recuos:
                md(f"""Na leitura com os recuos padrão da zona, a área útil de implantação cai para **{fmt_num(a_recuos)} m²**, mas a área pretendida de **{fmt_num(ref_area)} m²** continua sendo viável.""")
            else:
                md(f"""Na leitura com os recuos padrão da zona, a área útil de implantação cai para **{fmt_num(a_recuos)} m²**, de modo que esse passa a ser o limite físico de implantação.""")
            if not excedeu_area and ref_area <= a_recuos:
                md("""👉 **Neste caso, a área pretendida informada permanece viável nas duas leituras: tanto pela TO máxima da zona quanto pela implantação prática com recuos.**""")
            elif excedeu_area and ref_area <= a_recuos:
                md("""👉 **Neste caso, a área originalmente informada precisou ser ajustada, e a leitura final passa a considerar a área adotada como viável nas duas leituras.**""")
            else:
                md("""👉 **Neste caso, a leitura final deve respeitar o menor limite aplicável entre a TO máxima da zona e a implantação prática com recuos.**""")
        else:
            if not excedeu_area:
                md("""👉 **Neste caso, a área pretendida informada permanece viável pela TO máxima da zona.**""")
            else:
                md("""👉 **Neste caso, a leitura final deve respeitar o limite máximo pela TO da zona.**""")
    else:
        md("""Na leitura com a flexibilidade do art. 112, o aproveitamento do térreo pode chegar ao limite máximo permitido pela zona, desde que sejam respeitadas a TO, a TP e as demais exigências aplicáveis.""")

        if a_recuos is not None:
            md(f"""Na leitura com os recuos padrão da zona, a área útil de implantação fica em **{fmt_num(a_recuos)} m²**.""")
            md("""👉 **Neste caso, sem uma área pretendida informada, o estudo passa a apresentar os dois referenciais principais do lote: o limite máximo pela TO e o limite físico de implantação considerando os recuos.**""")
        else:
            md("""👉 **Neste caso, sem uma área pretendida informada, o estudo passa a apresentar o limite máximo pela TO como referencial principal do lote.**""")
