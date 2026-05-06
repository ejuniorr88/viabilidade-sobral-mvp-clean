from __future__ import annotations

from typing import Any

import streamlit as st


def md(text: str) -> None:
    st.markdown(text)


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


# Helpers adicionados para blindagem dos relatórios ZEIP/envelope físico
def _num(v: Any):
    try:
        if v is None or v == "":
            return None
        if isinstance(v, str):
            txt = v.strip().replace(".", "").replace(",", ".")
            if not txt:
                return None
            return float(txt)
        return float(v)
    except Exception:
        return None

def zone_key(value: Any) -> str:
    return str(value or "").strip().upper().replace("-", "_").replace(" ", "_")

def is_zeip(ctx: dict) -> bool:
    return zone_key(ctx.get("zone_sigla") or ctx.get("zone") or ctx.get("zone_title") or "").startswith("ZEIP")

def is_zeip9(ctx: dict) -> bool:
    keys = {zone_key(v) for v in (ctx.get("zone_sigla"), ctx.get("zone"), ctx.get("subzone_code"), ctx.get("zone_title")) if v is not None}
    return "ZEIP_9" in keys or ("ZEIP" in keys and "9" in keys)

def zeip_alert_text() -> str:
    return "**Atenção ZEIP/IPHAN:** por estar em ZEIP, intervenções podem exigir análise patrimonial específica e manifestação/aprovação do órgão competente, inclusive IPHAN quando aplicável."

def zeip9_alert_text() -> str:
    return "**Atenção especial — ZEIP_9:** este setor possui restrição específica quanto à construção de novos edifícios e à configuração dos lotes existentes. O resultado não deve ser tratado como permissão simples para obra nova sem confirmação do órgão competente."

def practical_ground_limit(ctx: dict):
    vals=[]
    for key in ("A_to", "A_recuos"):
        v=_num(ctx.get(key))
        if v is not None and v>0: vals.append(v)
    lot=_num(ctx.get("A")); tp=_num(ctx.get("A_perm_min"))
    if lot is not None and tp is not None: vals.append(max(lot-tp,0.0))
    return min(vals) if vals else None

def dimension_alerts(ctx: dict) -> list[str]:
    alerts=[]; rule=ctx.get("rule") or {}; area=_num(ctx.get("A")); front=_num(ctx.get("W"))
    area_min=_num(rule.get("area_min_lote_m2") or rule.get("area_lote_min_m2") or rule.get("lote_min_area_m2"))
    area_max=_num(rule.get("area_max_lote_m2") or rule.get("area_lote_max_m2") or rule.get("lote_max_area_m2"))
    testada_min=_num(rule.get("testada_min_m") or rule.get("testada_min_meio_m") or rule.get("testada_minima_m"))
    testada_max=_num(rule.get("testada_max_m") or rule.get("testada_max_meio_m"))
    if area is not None and area_min is not None and area < area_min:
        alerts.append(f"A área do lote informada ({fmt_num(area)} m²) está abaixo da área mínima cadastrada ({fmt_num(area_min)} m²). Essa condição não invalida automaticamente o estudo, mas exige conferência da situação cadastral do lote e da possibilidade de alteração de parcelamento junto ao órgão competente.")
    if area is not None and area_max is not None and area > area_max:
        alerts.append(f"A área do lote informada ({fmt_num(area)} m²) está acima da área máxima cadastrada ({fmt_num(area_max)} m²). Essa condição não invalida automaticamente o estudo, mas exige conferência da situação cadastral do lote e da possibilidade de alteração de parcelamento junto ao órgão competente.")
    if front is not None and testada_min is not None and front < testada_min:
        alerts.append(f"A testada informada ({fmt_num(front)} m) está abaixo da testada mínima cadastrada ({fmt_num(testada_min)} m). Conferir a situação cadastral e o enquadramento no licenciamento.")
    if front is not None and testada_max is not None and front > testada_max:
        alerts.append(f"A testada informada ({fmt_num(front)} m) está acima da testada máxima cadastrada ({fmt_num(testada_max)} m). Conferir a situação cadastral e o enquadramento no licenciamento.")
    return alerts
