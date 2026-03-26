from __future__ import annotations

import streamlit as _st

def render(ctx: dict) -> None:
    st = ctx.get("st", _st)
    st.markdown("---\n### 🚶 1️⃣1️⃣ O que preciso saber sobre a calçada?")
    st.markdown(
        "A análise não termina dentro do lote. Também existem regras para calçada, acesso ao imóvel, rebaixo de meio-fio e relação do lote com a rua. "
        "As figuras abaixo ajudam a visualizar esse padrão."
    )
    ctx['render_figuras_anexo_v'](ctx['rule'], is_corner=ctx['is_corner'])
