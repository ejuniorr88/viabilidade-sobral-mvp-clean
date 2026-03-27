from __future__ import annotations

import math
import streamlit as st


def md(text: str) -> None:
    st.markdown(text)


def fmt_num(v) -> str:
    try:
        if v is None or v == "":
            return "—"
        return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(v)


def fmt_pct(v) -> str:
    try:
        if v is None or v == "":
            return "—"
        val = float(v)
        return f"{val:.1f}%".replace(".", ",")
    except Exception:
        return str(v)
