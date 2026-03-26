from __future__ import annotations

import streamlit as _st


def render(ctx: dict) -> None:
    st = ctx.get("st", _st)
    st.markdown("---\n### 📌 1️⃣3️⃣ Resumo rápido final")
    st.markdown("**Se você quiser ver só o essencial deste terreno, este é o resumo principal:**")
    resumo_extra = ""
    if ctx['area_pedida'] is not None and ctx['A_considerada'] is not None:
        resumo_extra += f"\n- **Área pretendida informada:** {ctx['area_pedida_fmt']} m²"
        resumo_extra += f"\n- **Área adotada no relatório:** {ctx['A_considerada_fmt']} m²"
        if ctx['to_projeto_pct'] is not None:
            resumo_extra += f"\n- **TO efetiva considerada:** {ctx['to_projeto_pct_fmt']}"
        if ctx['A_livre'] is not None:
            resumo_extra += f"\n- **Área livre remanescente:** {ctx['A_livre_fmt']} m²"
        if ctx['A_ia_saldo'] is not None:
            resumo_extra += f"\n- **Saldo estimado pelo IA:** {ctx['A_ia_saldo_fmt']} m²"
    st.markdown(
        f"- **Uso analisado:** {ctx['uso_label']}\n"
        f"- **Zona:** {ctx['zone_title']}\n"
        f"- **Tipo de lote:** {ctx['tipo_lote']}\n"
        f"- **Via:** {ctx['via']}\n"
        f"- **Tipo de via:** {ctx['via_tipo']}\n\n"
        f"- **TO máxima:** {ctx['to_max_fmt']}\n"
        f"- **TP mínima:** {ctx['tp_min_fmt']}\n"
        f"- **IA máximo:** {ctx['ia_max_fmt']}\n"
        f"- **Altura máxima:** {ctx['gabarito_fmt']} m\n\n"
        f"- **Área máxima no térreo pela TO:** {ctx['A_to_fmt']} m²\n"
        f"- **Área permeável mínima:** {ctx['A_perm_min_fmt']} m²\n"
        f"- **Área total máxima estimada:** {ctx['A_total_fmt']} m²"
        f"{resumo_extra}"
    )
    if ctx['area_pedida'] is not None and ctx['A_considerada'] is not None:
        if ctx['excedeu_area']:
            st.markdown(
                f"👉 **Em resumo:** você informou **{ctx['area_pedida_fmt']} m²** no térreo, mas o relatório adotou **{ctx['A_considerada_fmt']} m²** para respeitar os limites urbanísticos do lote. "
                f"Com isso, a TO considerada ficou em **{ctx['to_projeto_pct_fmt']}**, a área livre remanescente em **{ctx['A_livre_fmt']} m²** e o saldo estimado pelo IA em **{ctx['A_ia_saldo_fmt']} m²**."
            )
        else:
            st.markdown(
                f"👉 **Em resumo:** o relatório considerou a área pretendida de **{ctx['A_considerada_fmt']} m²** no térreo. "
                f"Com isso, a TO considerada ficou em **{ctx['to_projeto_pct_fmt']}**, a área livre remanescente em **{ctx['A_livre_fmt']} m²** e o saldo estimado pelo IA em **{ctx['A_ia_saldo_fmt']} m²**."
            )
    else:
        st.markdown(
            f"👉 **Em resumo:** você pode ocupar até **{ctx['to_max_fmt']}** do lote no térreo; "
            f"precisa manter pelo menos **{ctx['tp_min_fmt']}** do terreno permeável; "
            f"a construção pode chegar até **{ctx['ia_max_fmt']}** vezes a área do lote no total; "
            "e a altura deve respeitar o limite da zona."
        )
