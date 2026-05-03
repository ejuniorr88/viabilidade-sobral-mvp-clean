from __future__ import annotations

import streamlit as st

from .common import md


def render(ctx: dict) -> None:
    md(
        "**As tabelas abaixo ajudam a interpretar as siglas usadas na análise de viabilidade. Elas mostram como a legislação classifica o uso pretendido para o terreno: adequado, inadequado, adequado apenas para determinados portes ou sujeito a análise como projeto especial. Em determinados casos, também é necessário observar o porte do empreendimento, já que classificações como AP e AP/AM indicam permissões vinculadas a faixas de área específicas.**"
    )
    col1, col2 = st.columns(2)
    with col1:
        md(
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
        md(
            "| Porte | Faixa (área construída total) |\n"
            "|---|---|\n"
            "| **Pequeno** | até **250 m²** |\n"
            "| **Médio** | de **250,01 m²** até **1.000 m²** |\n"
            "| **Grande** | de **1.000,01 m²** até **5.000 m²** |\n"
            "| **Projeto especial** | acima de **5.000 m²** |"
        )
