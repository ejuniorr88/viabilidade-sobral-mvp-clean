from __future__ import annotations

from typing import Any, Dict, Optional, Callable

import streamlit as st


def _to_float_ptbr(x: Any, default: float = 0.0) -> float:
    """Parse numbers coming either as float/int or as pt-BR strings like '300,00' or '1.234,56'."""
    if x is None:
        return default
    if isinstance(x, (int, float)):
        return float(x)
    try:
        s = str(x).strip()
        if s == "":
            return default
        # remove thousands separators and normalize decimal comma to dot
        s = s.replace(".", "").replace(",", ".")
        return float(s)
    except Exception:
        return default


def render_analise_section(
    calc: Dict[str, Any],
    lot_area: Any,
    built_ground: Any,
    pick_func: Callable[[Dict[str, Any], str], Any] | Callable[..., Any],
) -> None:
    """Renderiza a seção 5) Análise Urbanística.

    **PATCH mínimo**: apenas corrige parsing de números (ex.: '300,00') para evitar ValueError.
    Não altera layout do app.py.
    """
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
    # Área permeável prevista (melhor cenário): o que sobra no lote após a ocupação no térreo.
    # Obs.: na prática, parte dessa área pode virar piso impermeável; aqui o objetivo é dar
    # uma leitura automática quando o usuário não informa nada.
    permeable_area_f = max(0.0, lot_area_f - built_ground_f)

    # Pull values safely
    to_max_f = _to_float_ptbr(pick_func(rule, "to_max_pct", "to_max"), None) if pick_func else None
    ia_max_f = _to_float_ptbr(pick_func(rule, "ia_max", "ia_maximo"), None) if pick_func else None
    tp_min_f = _to_float_ptbr(pick_func(rule, "tp_min_pct", "tp_min"), None) if pick_func else None

    # Compute used metrics
    ia_utilizado = (built_ground_f / lot_area_f) if lot_area_f else 0.0
    to_utilizada = ((built_ground_f / lot_area_f) * 100) if lot_area_f else 0.0
    tp_prevista = ((permeable_area_f / lot_area_f) * 100) if lot_area_f else 0.0

    st.write(f"IA utilizado: **{ia_utilizado:.2f}**")
    st.write(f"TO utilizada: **{to_utilizada:.1f}%**")
    st.write(f"TP prevista: **{tp_prevista:.1f}%**")

    # Validations (only if rule has values)
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
