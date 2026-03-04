from __future__ import annotations

from typing import Any, Dict, Callable

import streamlit as st


def _to_float_ptbr(x: Any, default: float | None = 0.0) -> float | None:
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
    """Normaliza TO/TP vindos do Supabase.

    Suporta:
      - *_pct (0..100)
      - fração (0..1)
    """
    f = _to_float_ptbr(v, None)
    if f is None:
        return None
    # se parece fração
    if 0 <= f <= 1.0:
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

    lot_area_f = _to_float_ptbr(lot_area, 0.0) or 0.0
    built_ground_in = _to_float_ptbr(built_ground, 0.0) or 0.0
    calc["built_ground_input_m2"] = built_ground_in
    permeable_area_in = _to_float_ptbr(permeable_area, 0.0) or 0.0

    # regra (normalizada)
    to_max = _to_pct_from_rule(pick_func(rule, "to_max_pct", "to_max", default=None))
    ia_max = _to_float_ptbr(pick_func(rule, "ia_max", "ia_maximo", default=None), None)
    tp_min = _to_pct_from_rule(pick_func(rule, "tp_min_pct", "tp_min", default=None))

    # Se usuário deixou 0 no térreo, assumir o máximo permitido pela TO (e fundo obrigatório, se reduzir)
    adopted_ground = built_ground_in
    if adopted_ground <= 0 and lot_area_f > 0 and to_max is not None:
        by_to = lot_area_f * (to_max / 100.0)

        # limita pelo fundo (opção 2: zera frontal/laterais, fundo obrigatório)
        front = _to_float_ptbr(st.session_state.get("lot_front_m"), None)
        depth = _to_float_ptbr(st.session_state.get("lot_depth_m"), None)
        rec_fundos = _to_float_ptbr(pick_func(rule, "recuo_fundos_m", default=0.0), 0.0) or 0.0
        if front and depth and depth > rec_fundos:
            by_fundo = float(front) * (float(depth) - float(rec_fundos))
            adopted_ground = min(by_to, by_fundo)
        else:
            adopted_ground = by_to

    # Se permeável vier 0 (ou não informado), assume a TP mínima (para não mostrar 100% sem querer)
    adopted_permeable = permeable_area_in
    if adopted_permeable <= 0 and lot_area_f > 0 and tp_min is not None:
        adopted_permeable = lot_area_f * (tp_min / 100.0)

    ia_utilizado = (adopted_ground / lot_area_f) if lot_area_f else 0.0
    to_utilizada = ((adopted_ground / lot_area_f) * 100.0) if lot_area_f else 0.0
    tp_prevista = ((adopted_permeable / lot_area_f) * 100.0) if lot_area_f else 0.0

    # salvar no calc para o relatório
    calc["lot_area_m2"] = lot_area_f
    calc["built_ground_adopted_m2"] = adopted_ground
    calc["permeable_adopted_m2"] = adopted_permeable
    calc["ia_utilizado"] = ia_utilizado
    calc["to_utilizada_pct"] = to_utilizada
    calc["tp_prevista_pct"] = tp_prevista

    st.write(f"IA utilizado (considerando térreo adotado): **{ia_utilizado:.2f}**")
    st.write(f"TO utilizada: **{to_utilizada:.1f}%**")
    st.write(f"TP prevista: **{tp_prevista:.1f}%**")

    # validações
    if to_max is not None:
        st.success("✅ Taxa de Ocupação dentro do permitido") if to_utilizada <= to_max + 1e-9 else st.error("❌ Taxa de Ocupação EXCEDE o permitido")
    if ia_max is not None:
        st.success("✅ Índice de Aproveitamento dentro do permitido") if ia_utilizado <= ia_max + 1e-9 else st.error("❌ Índice de Aproveitamento EXCEDE o permitido")
    if tp_min is not None:
        st.success("✅ Taxa de Permeabilidade atende o mínimo") if tp_prevista + 1e-9 >= tp_min else st.warning("⚠️ Taxa de Permeabilidade abaixo do mínimo exigido.")
