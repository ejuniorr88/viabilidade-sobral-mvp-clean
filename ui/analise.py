from __future__ import annotations

from typing import Any, Callable, Dict, Optional
import streamlit as st


def _as_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        return float(x)
    except Exception:
        return None


def _normalize_pct(v: Optional[float]) -> Optional[float]:
    """
    Alguns dumps/schemas gravam percentuais como fração (0.6 = 60%).
    Outros gravam como percentual direto (60 = 60%).
    Heurística segura:
    - se 0 < v <= 1.0 -> tratar como fração e multiplicar por 100
    - se v > 1.0 -> já é percentual
    """
    if v is None:
        return None
    if 0 < v <= 1.0:
        return v * 100.0
    return v


def render_analise_section(
    calc: Dict[str, Any],
    lot_area: float,
    built_ground: float,
    pick_func: Callable[..., Any],
    as_float_func: Callable[[Any], Optional[float]] = _as_float,
) -> None:
    st.subheader("5) Análise Urbanística")

    rule = calc.get("rule")
    if not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar a análise.")
        return
    if not rule:
        st.info("Sem regra do Supabase — não é possível validar índices.")
        return

    # Inputs do usuário (persistentes)
    area_permeavel = st.number_input(
        "Área permeável prevista (m²)",
        min_value=0.0,
        value=float(st.session_state.get("area_permeavel_prevista_m2", 0.0)),
        step=1.0,
        key="area_permeavel_prevista_m2",
        help="Informe a área do lote que ficará permeável (grama, piso drenante etc.).",
    )

    area_total_construida = st.number_input(
        "Área total construída prevista (m²)",
        min_value=0.0,
        value=float(st.session_state.get("area_total_construida_m2", built_ground)),
        step=5.0,
        key="area_total_construida_m2",
        help="Para IA, use a soma das áreas de todos os pavimentos (não apenas o térreo).",
    )

    # Valores da regra (normalizando % quando vier como fração)
    to_max_pct = _normalize_pct(as_float_func(pick_func(rule, "to_max_pct", "to_max")))
    tp_min_pct = _normalize_pct(as_float_func(pick_func(rule, "tp_min_pct", "tp_min")))
    ia_max = as_float_func(pick_func(rule, "ia_max", "ia_maximo"))

    # Cálculos
    ia_utilizado = (area_total_construida / lot_area) if lot_area else 0.0
    to_utilizada_pct = ((built_ground / lot_area) * 100.0) if lot_area else 0.0
    tp_prevista_pct = ((area_permeavel / lot_area) * 100.0) if lot_area else 0.0

    st.write(f"IA utilizado: **{ia_utilizado:.2f}**")
    st.write(f"TO utilizada: **{to_utilizada_pct:.1f}%**")
    st.write(f"TP prevista: **{tp_prevista_pct:.1f}%**")

    # Validações
    if to_max_pct is not None:
        if to_utilizada_pct <= to_max_pct:
            st.success("✅ Taxa de Ocupação dentro do permitido")
        else:
            st.error("❌ Taxa de Ocupação EXCEDE o permitido")

    if ia_max is not None:
        if ia_utilizado <= ia_max:
            st.success("✅ Índice de Aproveitamento dentro do permitido")
        else:
            st.error("❌ Índice de Aproveitamento EXCEDE o permitido")

    if tp_min_pct is not None:
        if tp_prevista_pct >= tp_min_pct:
            st.success("✅ Taxa de Permeabilidade atende o mínimo")
        else:
            st.warning("⚠️ Taxa de Permeabilidade está abaixo do mínimo exigido.")
