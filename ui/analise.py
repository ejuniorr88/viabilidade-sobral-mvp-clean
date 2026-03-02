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


def _pick(rule: Dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in rule and rule.get(k) is not None:
            return rule.get(k)
    return None


def render_analise_section(
    *,
    calc: Dict[str, Any],
    lot_area: float,
    built_ground: float,
    pick_func: Optional[Callable[..., Any]] = None,
    as_float_func: Optional[Callable[[Any], Optional[float]]] = None,
    **_: Any,
) -> None:
    """Bloco 5: Análise Urbanística.

    - Mantém compatibilidade com chamadas antigas/nova (aceita kwargs extras).
    - Não muda layout de outros blocos.
    """

    st.subheader("5) Análise Urbanística")

    if not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar a análise.")
        return

    rule = calc.get("rule")
    if not rule:
        st.info("Sem regra do Supabase — não é possível validar índices.")
        return

    pick = pick_func or _pick
    as_float = as_float_func or _as_float

    # valores da regra
    to_max_f = as_float(pick(rule, "to_max_pct", "to_max"))
    ia_max_f = as_float(pick(rule, "ia_max", "ia_maximo"))
    tp_min_f = as_float(pick(rule, "tp_min_pct", "tp_min"))

    # cálculos
    ia_utilizado = (built_ground / lot_area) if lot_area else 0.0
    to_utilizada = ((built_ground / lot_area) * 100) if lot_area else 0.0

    # TP prevista ainda não foi coletada -> fica 0 por enquanto
    tp_prevista = 0.0

    st.write(f"IA utilizado: **{ia_utilizado:.2f}**")
    st.write(f"TO utilizada: **{to_utilizada:.1f}%**")
    st.write(f"TP prevista: **{tp_prevista:.1f}%**")

    # validações
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
            st.warning(
                "⚠️ Taxa de Permeabilidade ainda não foi informada / está abaixo do mínimo "
                "(precisamos do input de área permeável)."
            )
