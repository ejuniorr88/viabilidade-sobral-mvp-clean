from __future__ import annotations

import streamlit as _st


def render(ctx: dict) -> None:
    st = ctx.get("st", _st)
    st.markdown("---\n### 📍 1️⃣ Onde está localizado o terreno?")
    st.markdown("Aqui estão os dados principais usados nesta análise:")
    st.markdown(
        f"- **Uso informado:** {ctx['uso_label']}\n"
        f"- **Área do terreno:** {ctx['A_fmt']} m²\n"
        f"- **Dimensões:** {ctx['W_fmt']} m × {ctx['D_fmt']} m\n"
        f"- **Zona:** {ctx['zone']}\n"
        f"- **Subzona / setor:** {ctx['subzone_code']}\n"
        f"- **Tipo de lote:** {ctx['tipo_lote']}\n"
        f"- **Via:** {ctx['via']}\n"
        f"- **Tipo de via:** {ctx['via_tipo']}"
    )
    st.markdown("Essas informações são a base de todo o relatório.")
