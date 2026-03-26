from __future__ import annotations

import streamlit as _st


def render(ctx: dict) -> None:
    st = ctx.get("st", _st)
    st.markdown("---\n### 🚗 9️⃣ Preciso de vagas de estacionamento?")
    st.success("**Neste caso, não existe exigência mínima obrigatória de vagas de estacionamento.**")
    st.markdown("Essa exigência costuma aparecer em residências multifamiliares e em outras atividades previstas na lei.")
