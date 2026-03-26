from __future__ import annotations

import streamlit as _st


def render(ctx: dict) -> None:
    st = ctx.get("st", _st)
    st.markdown("---\n### 📘 3️⃣ Como funciona a leitura da adequabilidade no unifamiliar?")
    st.markdown(
        "**No unifamiliar, o resultado não depende só do nome da zona. Em alguns casos, também é preciso observar o tipo da via. "
        "Por isso, estas siglas ajudam a interpretar corretamente a viabilidade mostrada acima.**"
    )
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            "| Sigla | O que significa | Como interpretar |\n"
            "|---|---|---|\n"
            "| **A** | Adequado / permitido | Pode seguir com o projeto, respeitando as demais regras. |\n"
            "| **I** | Inadequado / não permitido | Em regra, não pode nesse local/condição. |\n"
            "| **AP** | Adequado (pequeno porte) | Pode, mas normalmente limitado a porte pequeno. |\n"
            "| **AM** | Adequado (médio porte) | Pode, mas normalmente limitado a porte médio. |\n"
            "| **AP/AM** | Depende do porte | Pode, mas depende se o caso é pequeno ou médio. |\n"
            "| **PE** | Projeto especial | Pode exigir análise específica e condições extras no licenciamento. |"
        )
    with col2:
        st.markdown(
            "| Porte | Faixa (área construída total) |\n"
            "|---|---|\n"
            "| **Pequeno** | até **250 m²** |\n"
            "| **Médio** | de **250,01 m²** até **1.000 m²** |\n"
            "| **Grande** | de **1.000,01 m²** até **5.000 m²** |\n"
            "| **Projeto especial** | acima de **5.000 m²** |"
        )
