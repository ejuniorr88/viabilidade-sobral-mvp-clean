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
        "Esse é o limite máximo permitido pela **Taxa de Ocupação (TO)**.\n\n"
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
