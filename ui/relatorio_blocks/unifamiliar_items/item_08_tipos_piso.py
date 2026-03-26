from __future__ import annotations

import streamlit as _st


def render(ctx: dict) -> None:
    st = ctx.get("st", _st)
    st.markdown("---\n### 🧱 7️⃣ Tipos de piso: o que conta como permeável?")
    st.markdown("Nem todo piso externo conta do mesmo jeito na permeabilidade. Veja como a lei trata isso:")
    st.markdown(
        ctx['md_table'](
            [
                ("Grama", "100%"),
                ("Brita solta / terra batida", "100%"),
                ("Piso drenante", "90%"),
                ("Bloco de concreto vazado (“piso verde”)", "60%"),
                ("Pedra portuguesa / intertravado", "25%"),
            ]
        )
    )
    st.markdown("Isso ajuda a entender que nem toda área “livre” do lote conta 100% como permeável.")
