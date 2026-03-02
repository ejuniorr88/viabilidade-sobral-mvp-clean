import streamlit as st

def render_relatorio_section(*args, **kwargs):
    st.subheader("6) Relatório Urbanístico")
    st.success("ui_relatorio carregou OK (import funcionando).")

__all__ = ["render_relatorio_section"]
