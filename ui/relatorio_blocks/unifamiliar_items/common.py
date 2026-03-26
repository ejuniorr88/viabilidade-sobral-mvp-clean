from __future__ import annotations

from typing import Any


def fmt_num(v: Any, dec: int = 2) -> str:
    try:
        if v is None:
            return "—"
        f = float(v)
        return f"{f:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(v)


def fmt_pct(v: Any, dec: int = 1) -> str:
    try:
        if v is None:
            return "—"
        f = float(v)
        return f"{f:.{dec}f}%"
    except Exception:
        return "—"


def md_table(rows: list[tuple[str, str]]) -> str:
    out = ["| Tipo de Piso | Percentual considerado permeável |", "|---|---:|"]
    for a, b in rows:
        out.append(f"| {a} | {b} |")
    return "\n".join(out)
