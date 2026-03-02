from __future__ import annotations

from typing import Any, Dict, Optional, Callable

import streamlit as st


def render_analise_section(
    *,
    calc: Dict[str, Any],
    pick_func: Callable[..., Any],
    as_float_func: Callable[[Any], Optional[float]],
) -> None:
    st.subheader("5) Análise Urbanística")

    rule = calc.get("rule")

    if not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar a análise.")
        return

    if not rule:
        st.info("Sem regra do Supabase — não é possível validar índices.")
        return

    lot_area = float(calc.get("lot_area_m2") or 0.0)
    built_ground = float(calc.get("built_ground_m2") or 0.0)

    area_perm_prev = st.number_input(
        "Área permeável prevista (m²)",
        min_value=0.0,
        value=float(calc.get("area_permeavel_prevista_m2") or 0.0),
        step=1.0,
    )
    calc["area_permeavel_prevista_m2"] = float(area_perm_prev)

    to_max_f = as_float_func(pick_func(rule, "to_max_pct", "to_max"))
    ia_max_f = as_float_func(pick_func(rule, "ia_max", "ia_maximo"))
    tp_min_f = as_float_func(pick_func(rule, "tp_min_pct", "tp_min"))

    ia_utilizado = (built_ground / lot_area) if lot_area > 0 else 0.0
    to_utilizada = ((built_ground / lot_area) * 100.0) if lot_area > 0 else 0.0
    tp_prevista = ((area_perm_prev / lot_area) * 100.0) if lot_area > 0 else 0.0

    st.write(f"IA utilizado: **{ia_utilizado:.2f}**")
    st.write(f"TO utilizada: **{to_utilizada:.1f}%**")
    st.write(f"TP prevista: **{tp_prevista:.1f}%**")

    if to_max_f is not None:
        if to_utilizada <= to_max_f:
            st.success("✅ Taxa de Ocupação dentro do permitido")
        else:
            st.error("❌ Taxa de Ocupação EXCEDE o permitido")

    if ia_max_f is not None:
        if ia_utilizado <= ia_max_f:
            st.success("✅ Índice de Aproveitamento dentro do permitido")
        else:
            st.error("❌ Índice de Aproveitamento EXCEDE o permitido")

    if tp_min_f is not None:
        if tp_prevista >= tp_min_f:
            st.success("✅ Taxa de Permeabilidade atende o mínimo")
        else:
            st.warning("⚠️ Taxa de Permeabilidade está abaixo do mínimo exigido.")
