from __future__ import annotations

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

    to_max = _to_float_ptbr(pick_func(rule, "to_max_pct", "to_max", default=None), None)
    ia_max = _to_float_ptbr(pick_func(rule, "ia_max", "ia_maximo", default=None), None)
    tp_min = _to_float_ptbr(pick_func(rule, "tp_min_pct", "tp_min", default=None), None)

    # Regra de negócio (MVP):
    # - Se o usuário deixar a área pretendida no térreo em branco/0,
    #   assumimos a TO máxima permitida (se existir na regra).
    assumed_max_to = False
    if (built_ground_f is None or built_ground_f <= 0.0) and (to_max is not None) and lot_area_f > 0:
        built_ground_f = (lot_area_f * float(to_max)) / 100.0
        assumed_max_to = True

    # Permeabilidade (MVP): NÃO é input.
    # Indicamos TP a partir da TO (estimativa simples):
    # TP% = 100% - TO%
    # (equivalente a permeável = lote - térreo)
    permeable_area_f = max(0.0, float(lot_area_f) - float(built_ground_f))

    ia_utilizado = (built_ground_f / lot_area_f) if lot_area_f else 0.0
    to_utilizada = ((built_ground_f / lot_area_f) * 100) if lot_area_f else 0.0
    tp_prevista = (100.0 - to_utilizada) if lot_area_f else 0.0

    if assumed_max_to:
        st.info(
            "Área pretendida no térreo = 0. "
            "Assumindo automaticamente a **TO máxima permitida** pela regra para o cálculo."
        )

    st.write(f"IA utilizado: **{ia_utilizado:.2f}**")
    st.write(f"TO utilizada: **{to_utilizada:.1f}%**")
    st.write(f"TP indicada (por TO): **{tp_prevista:.1f}%**")

    # Persistência no calc (para relatório)
    calc["ia_utilizado"] = float(ia_utilizado)
    calc["to_utilizada_pct"] = float(to_utilizada)
    calc["tp_prevista_pct"] = float(tp_prevista)
    calc["basic"] = {
        "lot_area_m2": float(lot_area_f),
        "built_ground_m2": float(built_ground_f),
        "permeable_area_m2": float(permeable_area_f),
        "ia_utilizado": float(ia_utilizado),
        "to_utilizada_pct": float(to_utilizada),
        "tp_prevista_pct": float(tp_prevista),
        "assumed_max_to": bool(assumed_max_to),
    }

    if to_max is not None:
        st.success("✅ Taxa de Ocupação dentro do permitido") if to_utilizada <= to_max else st.error("❌ Taxa de Ocupação EXCEDE o permitido")

    if ia_max is not None:
        st.success("✅ Índice de Aproveitamento dentro do permitido") if ia_utilizado <= ia_max else st.error("❌ Índice de Aproveitamento EXCEDE o permitido")

    if tp_min is not None:
        st.success("✅ Taxa de Permeabilidade atende o mínimo") if tp_prevista >= tp_min else st.warning("⚠️ Taxa de Permeabilidade abaixo do mínimo exigido.")
