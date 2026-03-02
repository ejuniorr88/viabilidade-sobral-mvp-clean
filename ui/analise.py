from __future__ import annotations

from typing import Any, Dict, Optional, Callable

import streamlit as st


def render_analise_section(
    *,
    calc: Dict[str, Any],
    lot_area: float,
    built_ground: float,
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

    to_max_f = as_float_func(pick_func(rule, "to_max_pct", "to_max"))
    ia_max_f = as_float_func(pick_func(rule, "ia_max", "ia_maximo"))
    tp_min_f = as_float_func(pick_func(rule, "tp_min_pct", "tp_min"))

    # normalizar percentuais
    if to_max_f is not None and to_max_f <= 1.0:
        to_max_pct = to_max_f * 100.0
    else:
        to_max_pct = to_max_f

    st_permeavel = st.number_input(
        "Área permeável prevista (m²)",
        min_value=0.0,
        value=float(st.session_state.get("area_permeavel_prevista_m2") or 0.0),
        step=1.0,
    )
    st.session_state.area_permeavel_prevista_m2 = float(st_permeavel)

    # Se usuário não informou built_ground, assume máximo pela TO (quando existir)
    if (built_ground is None or built_ground <= 0) and to_max_pct is not None:
        built_ground_eff = (lot_area * (to_max_pct / 100.0)) if lot_area else 0.0
    else:
        built_ground_eff = built_ground or 0.0

    ia_utilizado = (built_ground_eff / lot_area) if lot_area else 0.0
    to_utilizada = ((built_ground_eff / lot_area) * 100.0) if lot_area else 0.0
    tp_prevista = ((st_permeavel / lot_area) * 100.0) if lot_area else 0.0

    st.write(f"IA utilizado: **{ia_utilizado:.2f}**")
    st.write(f"TO utilizada: **{to_utilizada:.1f}%**")
    st.write(f"TP prevista: **{tp_prevista:.1f}%**")

    if to_max_pct is not None:
        if to_utilizada <= float(to_max_pct):
            st.success("✅ Taxa de Ocupação dentro do permitido")
        else:
            st.error("❌ Taxa de Ocupação EXCEDE o permitido")

    if ia_max_f is not None:
        if ia_utilizado <= float(ia_max_f):
            st.success("✅ Índice de Aproveitamento dentro do permitido")
        else:
            st.error("❌ Índice de Aproveitamento EXCEDE o permitido")

    if tp_min_f is not None:
        tp_min_pct = tp_min_f if tp_min_f <= 1.0 else tp_min_f / 100.0
        if tp_prevista >= tp_min_pct * 100.0:
            st.success("✅ Taxa de Permeabilidade atende o mínimo")
        else:
            st.warning("⚠️ Taxa de Permeabilidade está abaixo do mínimo exigido.")
