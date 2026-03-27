from __future__ import annotations

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


def md_table(headers: list[str], rows: list[list[str]]) -> None:
    if not headers:
        return

    table = "<table style='width:100%; border-collapse: collapse;'>"
    table += "<thead><tr>"
    for h in headers:
        table += (
            "<th style='text-align:left; padding:8px; border:1px solid #ddd;'>"
            f"{h}</th>"
        )
    table += "</tr></thead><tbody>"

    for row in rows:
        table += "<tr>"
        for cell in row:
            table += (
                "<td style='padding:8px; border:1px solid #ddd;'>"
                f"{cell}</td>"
            )
        table += "</tr>"

    table += "</tbody></table>"
    st.markdown(table, unsafe_allow_html=True)
