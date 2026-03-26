from __future__ import annotations

import streamlit as st


def md(text: str) -> None:
    st.markdown(text)


def formula_box(ctx: dict, text: str) -> None:
    ctx["_formula_box"](text)
