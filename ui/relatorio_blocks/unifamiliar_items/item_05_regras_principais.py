from __future__ import annotations

import streamlit as _st


def render(ctx: dict) -> None:
    st = ctx.get("st", _st)
    st.markdown("---\n### 📏 5️⃣ Regras principais para este terreno")
    st.markdown(
        "Depois de entender a zona, o próximo passo é ver as regras básicas do lote.\n\n"
        "Para este terreno, vale olhar principalmente:\n\n"
        "- ocupação máxima no térreo\n"
        "- área que precisa ficar livre\n"
        "- recuos\n"
        "- altura máxima\n"
        "- potencial total de construção"
    )
    st.markdown(
        f"**Resumo das regras**\n\n"
        f"- **TO máxima:** {ctx['to_max_fmt']}\n"
        f"- **TP mínima:** {ctx['tp_min_fmt']}\n"
        f"- **IA máximo:** {ctx['ia_max_fmt']}\n"
        f"- **IA mínimo:** {ctx['ia_min_texto']}\n"
        f"- **Recuos:** {ctx['recuos_resumo']}\n"
        f"- **Altura máxima:** {ctx['gabarito_fmt']} m"
    )
    st.markdown("Essas são as regras que mais impactam o projeto.")
