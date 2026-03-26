from __future__ import annotations

import streamlit as _st

from ..quadro_tecnico import render_quadro_tecnico


def render(ctx: dict) -> None:
    st = ctx.get("st", _st)
    st.markdown("---\n### 📋 1️⃣0️⃣ Quais medidas mínimas os ambientes precisam ter?")
    st.markdown(
        "Além das regras do lote, a legislação também traz medidas mínimas para alguns ambientes da edificação. "
        "Isso vale para itens como sala, quartos, cozinha, banheiro, área de serviço, garagem e escada."
    )
    render_quadro_tecnico()
