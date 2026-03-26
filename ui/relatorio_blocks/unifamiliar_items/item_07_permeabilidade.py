from __future__ import annotations

import streamlit as _st


def render(ctx: dict) -> None:
    st = ctx.get("st", _st)
    st.markdown("---\n### 🌿 7️⃣ Quanto preciso deixar livre?")
    if ctx['tp_min'] is None or ctx['A_perm_min'] is None:
        st.info("Sem TP mínima cadastrada para esta zona/uso.")
        return
    st.markdown(
        f"A zona exige **{ctx['tp_min_fmt']}** de área permeável.\n\n"
        f"👉 **{ctx['A_fmt']} m² × {ctx['tp_min_fmt']} = {ctx['A_perm_min_fmt']} m²** obrigatórios permeáveis\n\n"
        "Isso quer dizer que parte do terreno precisa continuar permitindo a infiltração da água da chuva no solo."
    )
    if ctx['A_considerada'] is not None and ctx['A_livre'] is not None:
        st.markdown("**Área livre considerando a área adotada no relatório**")
        st.markdown(
            f"Como o relatório adotou **{ctx['A_considerada_fmt']} m²** no térreo, a área livre remanescente no lote fica assim:\n\n"
            f"👉 **{ctx['A_fmt']} m² − {ctx['A_considerada_fmt']} m² = {ctx['A_livre_fmt']} m²**"
        )
        st.markdown(f"**Área livre remanescente no lote: {ctx['A_livre_fmt']} m²**")
        st.markdown(f"Desses, **{ctx['A_perm_min_fmt']} m²** precisam permanecer permeáveis.")
        if ctx['A_impermeavel_possivel'] is not None:
            st.markdown(
                f"Assim, restam:\n\n👉 **{ctx['A_livre_fmt']} m² − {ctx['A_perm_min_fmt']} m² = {ctx['A_impermeavel_possivel_fmt']} m²**\n\n"
                f"**Área que ainda pode receber piso impermeável: {ctx['A_impermeavel_possivel_fmt']} m²**"
            )
        leitura_tp = (
            f"como a área pretendida inicial de **{ctx['area_pedida_fmt']} m²** excedeu o limite adotado no relatório, os cálculos passaram a considerar **{ctx['A_considerada_fmt']} m²** no térreo"
            if ctx['excedeu_area'] and ctx['area_pedida'] is not None
            else f"os cálculos passaram a considerar a própria área pretendida informada, de **{ctx['A_considerada_fmt']} m²** no térreo"
        )
        st.markdown(
            f"👉 **Leitura prática:** {leitura_tp}. Com isso, a área livre remanescente fica em **{ctx['A_livre_fmt']} m²**, "
            f"dos quais **{ctx['A_perm_min_fmt']} m²** devem permanecer permeáveis para atender à exigência mínima da zona."
        )
        return
    st.markdown("**Ver cenários usando os máximos das opções**")
    if ctx['tp1'] is not None and ctx['A_op1_max'] is not None:
        a_rest, a_imperm = ctx['tp1']
        st.markdown("✅ **Cenário pela Opção 1 (recuos padrão)**")
        st.markdown(
            f"Se você utilizar **{ctx['A_op1_max_fmt']} m²** no térreo:\n\n"
            f"👉 Área restante no lote: **{ctx['A_fmt']} m² − {ctx['A_op1_max_fmt']} m² = {ctx['fmt_num'](a_rest)} m²**\n\n"
            f"Desses:\n\n"
            f"- **{ctx['A_perm_min_fmt']} m²** devem permitir infiltração no solo\n"
            f"- **{ctx['fmt_num'](a_imperm)} m²** podem receber piso impermeável"
        )
    if ctx['tp2'] is not None and ctx['A_op2_max'] is not None:
        a_rest, a_imperm = ctx['tp2']
        st.markdown("✅ **Cenário pela Opção 2 (Art. 112)**")
        st.markdown(
            f"Se você utilizar **{ctx['A_op2_max_fmt']} m²** no térreo:\n\n"
            f"👉 Área restante no lote: **{ctx['A_fmt']} m² − {ctx['A_op2_max_fmt']} m² = {ctx['fmt_num'](a_rest)} m²**\n\n"
            f"Desses:\n\n"
            f"- **{ctx['A_perm_min_fmt']} m²** devem permitir infiltração no solo\n"
            f"- **{ctx['fmt_num'](a_imperm)} m²** podem receber piso impermeável"
        )
    st.markdown(
        "**Leitura prática:** nas duas opções, o lote precisa manter a área permeável mínima. "
        "A diferença está em quanto sobra livre além desse mínimo."
    )
