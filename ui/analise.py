from __future__ import annotations

from typing import Any, Dict, Callable

import streamlit as st


def _to_float_ptbr(x: Any, default: float | None = 0.0) -> float | None:
    """Converte número pt-BR: '1.234,56' -> 1234.56.

    Retorna default se não conseguir.
    """
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

    lot_area_f = _to_float_ptbr(lot_area, 0.0) or 0.0
    built_ground_f = _to_float_ptbr(built_ground, 0.0) or 0.0
    permeable_area_f = _to_float_ptbr(permeable_area, 0.0) or 0.0

    ia_utilizado = (built_ground_f / lot_area_f) if lot_area_f else 0.0
    to_utilizada = ((built_ground_f / lot_area_f) * 100.0) if lot_area_f else 0.0
    tp_prevista = ((permeable_area_f / lot_area_f) * 100.0) if lot_area_f else 0.0

    # Persistência p/ relatório (evita NULL)
    calc["ia_utilizado"] = ia_utilizado
    calc["to_utilizada_pct"] = to_utilizada
    calc["tp_prevista_pct"] = tp_prevista
    calc["basic"] = {
        "ia": round(ia_utilizado, 6),
        "to": round(to_utilizada, 6),
        "tp": round(tp_prevista, 6),
        "lot_area_m2": lot_area_f,
        "built_ground_m2": built_ground_f,
        "permeable_area_m2": permeable_area_f,
    }

    st.write(f"IA utilizado: **{ia_utilizado:.2f}**")
    st.write(f"TO utilizada: **{to_utilizada:.1f}%**")
    st.write(f"TP prevista: **{tp_prevista:.1f}%**")

    rule = calc.get("rule")
    if not isinstance(rule, dict) or not rule:
        st.info("Sem regra do Supabase — cálculos gerados, mas sem validação.")
        return

    to_max = _to_float_ptbr(pick_func(rule, "to_max", "to_max_pct", default=None), None)
    ia_max = _to_float_ptbr(pick_func(rule, "ia_max", "ia_maximo", default=None), None)
    tp_min = _to_float_ptbr(pick_func(rule, "tp_min", "tp_min_pct", default=None), None)

    if to_max is not None:
        st.success("✅ Taxa de Ocupação dentro do permitido") if to_utilizada <= to_max else st.error(
            "❌ Taxa de Ocupação EXCEDE o permitido"
        )

    if ia_max is not None:
        st.success("✅ Índice de Aproveitamento dentro do permitido") if ia_utilizado <= ia_max else st.error(
            "❌ Índice de Aproveitamento EXCEDE o permitido"
        )

    if tp_min is not None:
        st.success("✅ Taxa de Permeabilidade atende o mínimo") if tp_prevista >= tp_min else st.warning(
            "⚠️ Taxa de Permeabilidade abaixo do mínimo exigido."
        )
