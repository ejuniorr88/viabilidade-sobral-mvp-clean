from __future__ import annotations

from typing import Any, Dict, Optional, Callable

import streamlit as st


def _as_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        return float(x)
    except Exception:
        return None


def render_analise_section(
    *,
    calc: Dict[str, Any],
    lote: Dict[str, Any],
    pick_func: Callable[..., Any],
) -> None:
    """
    Seção 5) Análise Urbanística

    Regras:
    - Só roda se calc["ok"] == True (apertou "Calcular viabilidade")
    - Usa os dados do lote vindos de `lote` (para não zerar por engano)
    - Valida TO/IA/TP somente quando existir valor na regra do Supabase
    """
    st.subheader("5) Análise Urbanística")

    if not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar a análise.")
        return

    rule = calc.get("rule")
    if not rule:
        st.info("Sem regra do Supabase — não é possível validar índices.")
        return

    # =============================
    # Dados do lote (entradas)
    # =============================
    lot_area = float(lote.get("lot_area") or 0.0)
    built_ground = float(lote.get("built_ground") or 0.0)

    # Área permeável prevista (m²) - input leve aqui para destravar TP
    area_permeavel = st.number_input(
        "Área permeável prevista (m²)",
        min_value=0.0,
        value=float(lote.get("area_permeavel") or 0.0),
        step=5.0,
        help="Informe quanto do lote ficará com área permeável (solo natural/grama/piso drenante etc.).",
        key="area_permeavel_input",
    )

    # Guardar para uso futuro (relatório, export, etc.)
    st.session_state.setdefault("lote", {})
    st.session_state.lote["area_permeavel"] = area_permeavel

    # =============================
    # Parâmetros (Supabase)
    # =============================
    to_max_f = _as_float(pick_func(rule, "to_max_pct", "to_max"))
    ia_max_f = _as_float(pick_func(rule, "ia_max", "ia_maximo"))
    tp_min_f = _as_float(pick_func(rule, "tp_min_pct", "tp_min"))

    # =============================
    # Cálculos
    # =============================
    if lot_area <= 0:
        st.error("Área do lote inválida. Preencha em **2) Dados do lote**.")
        return

    ia_utilizado = built_ground / lot_area
    to_utilizada = (built_ground / lot_area) * 100.0
    tp_prevista = (area_permeavel / lot_area) * 100.0 if lot_area else 0.0

    st.write(f"IA utilizado: **{ia_utilizado:.2f}**")
    st.write(f"TO utilizada: **{to_utilizada:.1f}%**")
    st.write(f"TP prevista: **{tp_prevista:.1f}%**")

    # =============================
    # Validações
    # =============================
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
