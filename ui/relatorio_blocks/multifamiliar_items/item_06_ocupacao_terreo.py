from __future__ import annotations

import streamlit as st

from .common import md, fmt_num, fmt_pct


def _fmt_pct_pt(v) -> str:
    return fmt_pct(v).replace('.', ',')


def render(ctx: dict) -> None:
    if ctx['to_max'] is None or ctx['A_to'] is None:
        st.info("Sem TO máxima cadastrada para esta zona/uso.")
        return

    to_txt = _fmt_pct_pt(ctx['to_max'])
    area_pedida = ctx.get('area_pedida')
    a_to = ctx['A_to']
    a_recuos = ctx.get('A_recuos')

    md(
        f"A zona permite ocupar até **{to_txt}** do terreno no térreo.\n\n"
        f"👉 **{fmt_num(ctx['A'])} m² × {to_txt} = {fmt_num(a_to)} m²**\n\n"
        "Esse é o limite máximo permitido pela Taxa de Ocupação (TO)."
    )

    if area_pedida is not None:
        if area_pedida <= a_to:
            md(
                f"👉 **Área pretendida informada: {fmt_num(area_pedida)} m².** Como esse valor está abaixo do limite máximo permitido, ele pode ser adotado como referência inicial para a implantação no térreo."
            )
        else:
            md(
                f"👉 **Área pretendida informada: {fmt_num(area_pedida)} m².** Como esse valor ultrapassa o limite máximo permitido pela TO, ele não pode ser adotado integralmente como referência para a implantação no térreo."
            )

    md(
        "Como complemento a essa verificação, também é importante analisar a área que efetivamente cabe no lote, considerando os recuos aplicáveis."
    )

    md(
        "Art. 112. Será aplicado, para as atividades atrativas de vizinhança de pequeno porte e para o uso residencial unifamiliar, a flexibilidade quanto aos recuos de frente e laterais, podendo zerar, desde que observado o cumprimento da Taxa de Permeabilidade Mínima e da Taxa de Ocupação Máxima da zona em que se encontra."
    )

    md(
        "👉 Na prática: para residência unifamiliar, a norma permite encostar nas laterais e alinhar na frente, desde que o projeto continue respeitando a TO máxima e a TP mínima."
    )

    md("A partir disso, este lote pode ser lido de duas formas:")

    md("✅ **Opção principal — aproveitando a flexibilidade da lei**")
    md(
        "Para este caso, a legislação admite zerar o recuo frontal e os recuos laterais.\n\n"
        "Assim, o térreo pode aproveitar melhor a área do lote, desde que continue respeitando a TO e a TP.\n\n"
        f"👉 **Térreo máximo nesta opção: {fmt_num(a_to)} m²**"
    )

    if area_pedida is not None:
        if area_pedida <= a_to:
            md(
                f"👉 Como a área pretendida informada foi de **{fmt_num(area_pedida)} m²**, ela cabe dentro desse limite máximo."
            )
        else:
            md(
                f"👉 Como a área pretendida informada foi de **{fmt_num(area_pedida)} m²**, ela ultrapassa esse limite máximo."
            )

    md("⚠️ O recuo de fundo e as demais exigências urbanísticas aplicáveis continuam precisando ser respeitados.")

    if a_recuos is not None:
        md("✅ **Opção alternativa — adotando os recuos da zona**")
        md("Caso se opte por seguir os recuos padrão da zona, a implantação prática fica assim:")
        md(f"Frontal: {fmt_num(ctx['rec_fr'])} m")
        md(f"Laterais: {fmt_num(ctx['rec_lat'])} m cada")
        md(f"Fundo: {fmt_num(ctx['rec_fun'])} m")
        md("Com isso, a área útil de implantação no térreo passa a ser:")
        md(f"Largura útil: {fmt_num(ctx['W_util'])} m")
        md(f"Profundidade útil: {fmt_num(ctx['D_util'])} m")
        md(f"👉 **{fmt_num(ctx['W_util'])} × {fmt_num(ctx['D_util'])} = {fmt_num(a_recuos)} m²**")
        md(
            f"👉 Nesse cenário, mesmo que a zona permita até **{fmt_num(a_to)} m²** pela TO, o limite físico de implantação, considerando os recuos, fica em **{fmt_num(a_recuos)} m²**."
        )

        if area_pedida is not None:
            if area_pedida <= a_recuos:
                md(
                    f"👉 Como a área pretendida informada foi de **{fmt_num(area_pedida)} m²**, ela também cabe dentro desse limite físico."
                )
            else:
                md(
                    f"👉 Como a área pretendida informada foi de **{fmt_num(area_pedida)} m²**, ela ultrapassa esse limite físico de implantação."
                )

    md("**Leitura prática**")
    md(f"Pela Taxa de Ocupação (TO), o lote pode ocupar até **{fmt_num(a_to)} m²** no térreo.")

    if area_pedida is not None:
        if area_pedida <= a_to:
            md(f"Na leitura com a flexibilidade do art. 112, a área pretendida de **{fmt_num(area_pedida)} m²** é viável.")
        else:
            md(f"Na leitura com a flexibilidade do art. 112, a área pretendida de **{fmt_num(area_pedida)} m²** não é viável, pois ultrapassa o limite máximo permitido pela zona.")

        if a_recuos is not None:
            if area_pedida <= a_recuos:
                md(
                    f"Na leitura com os recuos padrão da zona, a área útil de implantação cai para **{fmt_num(a_recuos)} m²**, mas a área pretendida de **{fmt_num(area_pedida)} m²** continua sendo viável."
                )
                if area_pedida <= a_to:
                    md(
                        f"👉 Neste caso, a área pretendida informada permanece viável nas duas leituras: tanto pela TO máxima da zona quanto pela implantação prática com recuos."
                    )
                else:
                    md(
                        f"👉 Neste caso, a área pretendida informada não cabe no limite máximo da TO, embora caiba fisicamente na implantação com recuos."
                    )
            else:
                md(
                    f"Na leitura com os recuos padrão da zona, a área útil de implantação cai para **{fmt_num(a_recuos)} m²**, e a área pretendida de **{fmt_num(area_pedida)} m²** não cabe dentro desse limite físico."
                )
                if area_pedida <= a_to:
                    md(
                        f"👉 Neste caso, a área pretendida informada cabe no limite máximo da TO, mas não na implantação prática com recuos."
                    )
                else:
                    md(
                        f"👉 Neste caso, a área pretendida informada não é viável nem pela TO máxima da zona nem pela implantação prática com recuos."
                    )
        else:
            if area_pedida <= a_to:
                md(
                    f"👉 Neste caso, a área pretendida informada permanece viável pela TO máxima da zona."
                )
            else:
                md(
                    f"👉 Neste caso, a área pretendida informada não é viável pela TO máxima da zona."
                )
    else:
        md(
            "Na leitura com a flexibilidade do art. 112, o aproveitamento do térreo pode chegar ao limite máximo permitido pela zona, desde que sejam respeitadas a TO, a TP e as demais exigências aplicáveis."
        )
        if a_recuos is not None:
            md(
                f"Na leitura com os recuos padrão da zona, a área útil de implantação fica em **{fmt_num(a_recuos)} m²**."
            )
        md(
            "👉 Neste caso, sem uma área pretendida informada, o estudo passa a apresentar os dois referenciais principais do lote: o limite máximo pela TO e o limite físico de implantação considerando os recuos."
        )
