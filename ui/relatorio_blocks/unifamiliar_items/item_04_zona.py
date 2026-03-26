from __future__ import annotations

import streamlit as _st


def render(ctx: dict) -> None:
    st = ctx.get("st", _st)
    st.markdown("---\n### 🧭 4️⃣ O que essa zona permite neste terreno?")
    if ctx['desc'] and ctx['desc'].get('description_text'):
        st.markdown(f"**{ctx['zone_title']}**")
        st.markdown(str(ctx['desc'].get('description_text')))
    else:
        st.markdown(
            f"- **Zona:** {ctx['zone'] or '—'}\n"
            f"- **Via do terreno:** {ctx['via']}\n"
            f"- **Tipo de via:** {ctx['via_tipo']}"
        )
    st.markdown("**É essa leitura da zona que ajuda a entender o que pode ser implantado no lote e com qual porte.**")
