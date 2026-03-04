from __future__ import annotations

import math
from typing import Any, Dict, Callable

import streamlit as st


def _to_float_ptbr(x: Any, default: float = 0.0) -> float:
    if x is None:
        return default
    if isinstance(x, (int, float)):
        return float(x)
    try:
        s = str(x).strip()
        if s == "":
            return default
        s = s.replace(".", "").replace(",", ".")
        return float(s)
    except Exception:
        return default


def _to_pct_from_rule(v: Any) -> float | None:
    """Normaliza TO/TP do schema:
    - se vier em % (ex.: 60) retorna 60
    - se vier em fração (ex.: 0.6) retorna 60
    """
    if v is None:
        return None
    f = _to_float_ptbr(v, default=float("nan"))
    if math.isnan(f):
        return None
    if 0.0 <= f <= 1.0:
        return f * 100.0
    return f


def render_analise_section(
    calc: Dict[str, Any],
    *,
    lot_area: Any,
    built_ground: Any,
    permeable_area: Any,
    pick_func: Callable[..., Any],
) -> None:
    st.subheader("5) Análise Urbanística")

    if not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar a análise.")
        return

    rule = calc.get("rule")
    if not rule:
        st.info("Sem regra do Supabase — não é possível validar índices.")
        return

    lot_area_f = _to_float_ptbr(lot_area, 0.0)
    built_ground_f = _to_float_ptbr(built_ground, 0.0)
    permeable_area_f = _to_float_ptbr(permeable_area, 0.0)

    to_max_raw = pick_func(rule, "to_max_pct", "to_max", default=None)
    tp_min_raw = pick_func(rule, "tp_min_pct", "tp_min", default=None)
    ia_max = _to_float_ptbr(pick_func(rule, "ia_max", default=None), None)

    to_max = _to_pct_from_rule(to_max_raw)
    tp_min = _to_pct_from_rule(tp_min_raw)

    ia_utilizado = (built_ground_f / lot_area_f) if lot_area_f else 0.0
    to_utilizada = ((built_ground_f / lot_area_f) * 100) if lot_area_f else 0.0
    tp_prevista = ((permeable_area_f / lot_area_f) * 100) if lot_area_f else 0.0

    # Persistir para o relatório (sem alterar layout do app)
    calc["basic"] = {
        "lot_area_m2": lot_area_f,
        "built_ground_m2": built_ground_f,
        "permeable_area_m2": permeable_area_f,
        "ia": ia_utilizado,
        "to": to_utilizada,
        "tp": tp_prevista,
    }

    st.write(f"IA utilizado (considerando térreo adotado): **{ia_utilizado:.2f}**")
    st.write(f"TO utilizada: **{to_utilizada:.1f}%**")
    st.write(f"TP prevista: **{tp_prevista:.1f}%**")

    if to_max is not None:
        st.success("✅ Taxa de Ocupação dentro do permitido") if to_utilizada <= to_max else st.error("❌ Taxa de Ocupação EXCEDE o permitido")

    if ia_max is not None:
        st.success("✅ Índice de Aproveitamento dentro do permitido") if ia_utilizado <= ia_max else st.error("❌ Índice de Aproveitamento EXCEDE o permitido")

    if tp_min is not None:
        st.success("✅ Taxa de Permeabilidade atende o mínimo") if tp_prevista >= tp_min else st.warning("⚠️ Taxa de Permeabilidade abaixo do mínimo exigido.")
