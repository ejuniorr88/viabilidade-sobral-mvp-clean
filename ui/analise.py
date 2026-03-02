from __future__ import annotations

from typing import Any, Dict, Optional
import streamlit as st


def _as_float(x: Any) -> Optional[float]:
    if x is None or x == "":
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


def render_analise_section(**kwargs: Any) -> None:
    """
    Seção 5) Análise Urbanística

    ✅ Robustez:
    - aceita **kwargs para evitar TypeError quando o app.py mudar.
    - busca dados por nomes comuns (calc, lot_area, built_ground, area_permeavel_prevista).
    """
    st.subheader("5) Análise Urbanística")

    calc: Dict[str, Any] = kwargs.get("calc") or st.session_state.get("calc", {}) or {}
    rule: Optional[Dict[str, Any]] = calc.get("rule") if isinstance(calc, dict) else None

    lot_area = kwargs.get("lot_area", st.session_state.get("lot_area"))
    built_ground = kwargs.get("built_ground", st.session_state.get("built_ground"))
    area_perm = kwargs.get("area_permeavel_prevista", st.session_state.get("area_permeavel_prevista"))

    lot_area_f = float(lot_area) if lot_area not in (None, "") else 0.0
    built_ground_f = float(built_ground) if built_ground not in (None, "") else 0.0
    area_perm_f = float(area_perm) if area_perm not in (None, "") else 0.0

    if not calc or not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar a análise.")
        return
    if not rule:
        st.info("Sem regra do Supabase — não é possível validar índices.")
        return

    # se não informar área pretendida, assume o máximo pela TO
    if built_ground_f <= 0 and lot_area_f > 0:
        to_max_pct = _as_float(_pick(rule, "to_max_pct", "to_max"))
        if to_max_pct is not None:
            built_ground_f = lot_area_f * (to_max_pct / 100.0)

    to_max_f = _as_float(_pick(rule, "to_max_pct", "to_max"))
    ia_max_f = _as_float(_pick(rule, "ia_max", "ia_maximo"))
    tp_min_f = _as_float(_pick(rule, "tp_min_pct", "tp_min"))

    ia_utilizado = (built_ground_f / lot_area_f) if lot_area_f else 0.0
    to_utilizada = ((built_ground_f / lot_area_f) * 100.0) if lot_area_f else 0.0
    tp_prevista = ((area_perm_f / lot_area_f) * 100.0) if lot_area_f else 0.0

    st.write(f"IA utilizado: **{ia_utilizado:.2f}**")
    st.write(f"TO utilizada: **{to_utilizada:.1f}%**")
    st.write(f"TP prevista: **{tp_prevista:.1f}%**")

    if to_max_f is not None:
        st.success("✅ Taxa de Ocupação dentro do permitido") if to_utilizada <= to_max_f + 1e-9 else st.error("❌ Taxa de Ocupação EXCEDE o permitido")
    if ia_max_f is not None:
        st.success("✅ Índice de Aproveitamento dentro do permitido") if ia_utilizado <= ia_max_f + 1e-9 else st.error("❌ Índice de Aproveitamento EXCEDE o permitido")
    if tp_min_f is not None:
        st.success("✅ Taxa de Permeabilidade atende o mínimo") if tp_prevista >= tp_min_f - 1e-9 else st.warning("⚠️ Taxa de Permeabilidade está abaixo do mínimo exigido.")
