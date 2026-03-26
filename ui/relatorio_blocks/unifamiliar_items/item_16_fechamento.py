from __future__ import annotations

import streamlit as _st


def render(ctx: dict) -> None:
    st = ctx.get("st", _st)
    st.markdown("---\n### ✅ 1️⃣5️⃣ Fechamento final")
    st.markdown(
        "Este relatório foi pensado para ajudar a entender o terreno de forma mais simples.\n\n"
        "Na etapa de projeto e aprovação, ainda será preciso conferir os detalhes completos no licenciamento."
    )

    with st.expander("Ver regra completa (JSON)"):
        st.json(ctx['rule'])
