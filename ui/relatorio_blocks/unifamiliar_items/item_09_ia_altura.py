from __future__ import annotations

import streamlit as _st


def render(ctx: dict) -> None:
    st = ctx.get("st", _st)
    st.markdown("---\n### 🏢 8️⃣ Posso construir mais andares?")
    if ctx['ia_max'] is None or ctx['A_total'] is None:
        st.info("Sem IA máximo cadastrado para esta zona/uso.")
    else:
        st.markdown(
            f"Além da ocupação no térreo, a zona também define o potencial construtivo total do lote por meio do **Índice de Aproveitamento (IA)**.\n\n"
            f"Se o IA máximo da zona for **{ctx['ia_max_fmt']}**, então o potencial construtivo total do lote será:\n\n"
            f"👉 **{ctx['A_fmt']} m² × {ctx['ia_max_fmt']} = {ctx['A_total_fmt']} m²**\n\n"
            f"Esse é o total que pode ser distribuído entre térreo e pavimentos superiores, respeitando também os demais parâmetros urbanísticos."
        )
        if ctx['A_considerada'] is not None and ctx['A_ia_saldo'] is not None:
            st.markdown(
                f"Como o relatório adotou **{ctx['A_considerada_fmt']} m²** no térreo, o saldo estimado para crescer acima fica assim:\n\n"
                f"👉 **{ctx['A_total_fmt']} m² − {ctx['A_considerada_fmt']} m² = {ctx['A_ia_saldo_fmt']} m²**\n\n"
                f"**Saldo estimado para pavimentos superiores: {ctx['A_ia_saldo_fmt']} m²**"
            )
            st.markdown(
                f"👉 **Leitura prática:** considerando a área adotada de **{ctx['A_considerada_fmt']} m²** no térreo, ainda restam **{ctx['A_ia_saldo_fmt']} m²** de potencial construtivo pelo IA para crescimento em pavimentos superiores, desde que o projeto respeite também altura máxima, recuos, ventilação, iluminação, circulação e demais exigências aplicáveis."
            )
    if ctx['gabarito_m'] is not None:
        st.markdown(f"**Altura máxima da zona:** {ctx['gabarito_fmt']} m")
        if ctx['pav_est'] is not None:
            st.markdown(
                f"**Exemplo simples para ter uma noção de andares:** adotando um pé-direito médio de **3,00 m por pavimento**, "
                f"a altura máxima de **{ctx['gabarito_fmt']} m** pode permitir, em média, algo próximo de **{ctx['pav_est']} pavimentos**.\n\n"
                "👉 Isso é apenas uma referência inicial. Na prática, a quantidade real de andares depende também da laje, cobertura, "
                "platibanda, caixa d’água e da forma como o projeto será desenvolvido."
            )
