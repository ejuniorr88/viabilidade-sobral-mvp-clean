from __future__ import annotations

import streamlit as st

from .common import md


def render(ctx: dict) -> None:
    st.success("**Neste caso, não existe exigência mínima obrigatória de vagas de estacionamento.**")
    md("Essa exigência costuma aparecer em residências multifamiliares e em outras atividades previstas na lei.")
