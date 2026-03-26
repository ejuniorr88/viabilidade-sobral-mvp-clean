from __future__ import annotations

import streamlit as _st


def render(ctx: dict) -> None:
    st = ctx.get("st", _st)
    st.markdown("---\n### 📐 6️⃣ Quanto posso ocupar no térreo?")
    if ctx['to_max'] is None or ctx['A_to'] is None:
        st.info("Sem TO máxima cadastrada para esta zona/uso.")
        return
    st.markdown(
        f"A zona permite ocupar até **{ctx['to_max_fmt']}** do terreno no térreo.\n\n"
        f"👉 **{ctx['A_fmt']} m² × {ctx['to_max_fmt']} = {ctx['A_to_fmt']} m²**\n\n"
        "Esse é o limite máximo permitido pela **Taxa de Ocupação (TO)**.\n\n"
        "Mas aqui tem um ponto importante: uma coisa é o limite da zona no papel, e outra é o que realmente cabe dentro do lote depois de respeitar os recuos.\n\n"
        "Por isso, além do percentual permitido, também vale olhar a área que sobra de forma prática dentro do terreno."
    )
    st.markdown(
        "> **Art. 112.** Será aplicado, para as atividades atrativas de vizinhança de pequeno porte e para o uso residencial unifamiliar, "
        "a flexibilidade quanto aos recuos de frente e laterais, podendo zerar, desde que observado o cumprimento da Taxa de Permeabilidade Mínima "
        "e da Taxa de Ocupação Máxima da zona em que se encontra."
    )
    st.markdown(
        "👉 **Na prática:** para residência unifamiliar, a norma permite encostar nas laterais e alinhar na frente, desde que o projeto continue respeitando a **TO máxima** e a **TP mínima**."
    )
    st.markdown("Agora veja duas possibilidades de leitura:")

    st.markdown("✅ **Opção principal — aproveitando a flexibilidade da lei**")
    st.markdown(
        "Para este caso, a legislação admite **zerar recuo frontal e laterais**.\n\n"
        "Assim, o térreo pode aproveitar melhor a área do lote, desde que continue respeitando TO e TP.\n\n"
        f"👉 **Térreo máximo nesta opção:** **{ctx['A_to_fmt']} m²**\n\n"
        "⚠️ O recuo de fundo e as demais exigências aplicáveis continuam precisando ser respeitados."
    )

    if ctx['A_recuos'] is not None:
        st.markdown("✅ **Opção alternativa — adotando os recuos da zona**")
        st.markdown(f"- **Frontal:** {ctx['rec_fr_fmt']} m")
        st.markdown(f"- **Laterais:** {ctx['rec_lat_fmt']} m cada")
        st.markdown(f"- **Fundo:** {ctx['rec_fun_fmt']} m")
        st.markdown(f"- **Largura útil:** {ctx['W_util_fmt']} m")
        st.markdown(f"- **Profundidade útil:** {ctx['D_util_fmt']} m")
        st.markdown(f"👉 **{ctx['W_util_fmt']} × {ctx['D_util_fmt']} = {ctx['A_recuos_fmt']} m²**")
        st.markdown(
            f"👉 Neste cenário, mesmo que a zona permita até **{ctx['A_to_fmt']} m²**, o limite físico pelos recuos fica em **{ctx['A_recuos_fmt']} m²**."
        )
        st.markdown(
            f"**Leitura prática:** pela TO, o lote pode ocupar até **{ctx['A_to_fmt']} m²** no térreo. Mas, se você optar por seguir os recuos da zona, a implantação prática cai para **{ctx['A_recuos_fmt']} m²**."
        )
