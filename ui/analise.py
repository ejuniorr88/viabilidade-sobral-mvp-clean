from __future__ import annotations

from typing import Any, Dict, Callable, Optional

import streamlit as st


def _to_float_ptbr(x: Any, default: Optional[float] = 0.0) -> Optional[float]:
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


def _norm_pct(rule: Dict[str, Any], pick_func: Callable[..., Any], pct_key: str, frac_key: str) -> Optional[float]:
    v_pct = pick_func(rule, pct_key, default=None)
    v_pct_f = _to_float_ptbr(v_pct, None)
    if v_pct_f is not None:
        return float(v_pct_f)
    v_frac = pick_func(rule, frac_key, default=None)
    v_frac_f = _to_float_ptbr(v_frac, None)
    if v_frac_f is None:
        return None
    return float(v_frac_f) * 100.0


def _min0(x: float) -> float:
    return x if x > 0 else 0.0


def compute_report_numbers(*, lot_area: float, testada: float, profundidade: float, rule: Dict[str, Any], pick_func: Callable[..., Any]) -> Dict[str, Any]:
    to_max_pct = _norm_pct(rule, pick_func, "to_max_pct", "to_max")
    tp_min_pct = _norm_pct(rule, pick_func, "tp_min_pct", "tp_min")
    ia_max = _to_float_ptbr(pick_func(rule, "ia_max", default=None), None)

    rf = float(_to_float_ptbr(pick_func(rule, "recuo_frontal_m", default=0.0), 0.0) or 0.0)
    rl = float(_to_float_ptbr(pick_func(rule, "recuo_lateral_m", default=0.0), 0.0) or 0.0)
    rfd = float(_to_float_ptbr(pick_func(rule, "recuo_fundos_m", default=0.0), 0.0) or 0.0)

    gabarito_m = _to_float_ptbr(pick_func(rule, "gabarito_m", default=None), None)
    gabarito_pav = pick_func(rule, "gabarito_pav", default=None)
    try:
        gabarito_pav = int(gabarito_pav) if gabarito_pav is not None else None
    except Exception:
        gabarito_pav = None

    area_to_max = (lot_area * (to_max_pct / 100.0)) if (to_max_pct is not None) else None
    area_total_max = (lot_area * ia_max) if (ia_max is not None) else None
    area_perm_min = (lot_area * (tp_min_pct / 100.0)) if (tp_min_pct is not None) else None

    w_util = _min0(testada - 2.0 * rl)
    d_util = _min0(profundidade - rf - rfd)
    area_recuos = w_util * d_util
    area_op1 = min(area_recuos, area_to_max) if area_to_max is not None else area_recuos

    d2 = _min0(profundidade - rfd)
    area_fundo = _min0(testada) * d2
    area_op2 = min(area_fundo, area_to_max) if area_to_max is not None else area_fundo

    def tp_pack(area_terreo: float) -> Dict[str, Any]:
        area_livre = _min0(lot_area - area_terreo)
        if area_perm_min is None:
            return {"area_livre": area_livre, "area_perm_min": None, "area_imperm_max": None, "area_perm_max_possivel": area_livre}
        return {
            "area_livre": area_livre,
            "area_perm_min": float(area_perm_min),
            "area_imperm_max": float(area_livre - area_perm_min),
            "area_perm_max_possivel": area_livre,
        }

    return {
        "inputs": {"lot_area_m2": lot_area, "testada_m": testada, "profundidade_m": profundidade},
        "rule_norm": {
            "to_max_pct": to_max_pct,
            "tp_min_pct": tp_min_pct,
            "ia_max": ia_max,
            "recuo_frontal_m": rf,
            "recuo_lateral_m": rl,
            "recuo_fundos_m": rfd,
            "gabarito_m": gabarito_m,
            "gabarito_pav": gabarito_pav,
        },
        "limites": {
            "area_max_terreo_por_TO": area_to_max,
            "area_total_max_por_IA": area_total_max,
            "area_permeavel_min_por_TP": area_perm_min,
        },
        "opcao1": {
            "largura_util_m": w_util,
            "profundidade_util_m": d_util,
            "area_max_por_recuos_m2": area_recuos,
            "area_terreo_max_m2": area_op1,
            "tp": tp_pack(area_op1),
        },
        "opcao2": {
            "profundidade_util_m": d2,
            "area_max_por_fundo_m2": area_fundo,
            "area_terreo_max_m2": area_op2,
            "tp": tp_pack(area_op2),
        },
    }


def render_analise_section(calc: Dict[str, Any], *, lot_area: Any, built_ground: Any, permeable_area: Any, pick_func: Callable[..., Any]) -> None:
    st.subheader("5) Análise Urbanística")

    if not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar a análise.")
        return

    rule = calc.get("rule")
    if not rule:
        st.info("Sem regra do Supabase — não é possível validar índices.")
        return

    lot_area_f = float(_to_float_ptbr(lot_area, 0.0) or 0.0)
    built_ground_in = float(_to_float_ptbr(built_ground, 0.0) or 0.0)
    permeable_in = float(_to_float_ptbr(permeable_area, 0.0) or 0.0)

    testada = float(_to_float_ptbr(st.session_state.get("lot_front_m"), 0.0) or 0.0)
    profundidade = float(_to_float_ptbr(st.session_state.get("lot_depth_m"), 0.0) or 0.0)

    report = compute_report_numbers(lot_area=lot_area_f, testada=testada, profundidade=profundidade, rule=rule, pick_func=pick_func)
    calc["report"] = report

    built_ground_eff = built_ground_in if built_ground_in > 0 else float(report["opcao2"]["area_terreo_max_m2"])
    permeable_eff = permeable_in if permeable_in > 0 else max(0.0, lot_area_f - built_ground_eff)

    ia_utilizado = (built_ground_eff / lot_area_f) if lot_area_f else 0.0
    to_utilizada = ((built_ground_eff / lot_area_f) * 100.0) if lot_area_f else 0.0
    tp_prevista = ((permeable_eff / lot_area_f) * 100.0) if lot_area_f else 0.0

    calc["ia_utilizado"] = ia_utilizado
    calc["to_utilizada_pct"] = to_utilizada
    calc["tp_prevista_pct"] = tp_prevista

    st.write(f"IA utilizado (considerando térreo adotado): **{ia_utilizado:.2f}**")
    st.write(f"TO utilizada: **{to_utilizada:.1f}%**")
    st.write(f"TP prevista: **{tp_prevista:.1f}%**")

    to_max = report["rule_norm"]["to_max_pct"]
    ia_max = report["rule_norm"]["ia_max"]
    tp_min = report["rule_norm"]["tp_min_pct"]

    if to_max is not None:
        st.success("✅ Taxa de Ocupação dentro do permitido") if to_utilizada <= to_max else st.error("❌ Taxa de Ocupação EXCEDE o permitido")
    if ia_max is not None:
        st.success("✅ Índice de Aproveitamento dentro do permitido") if ia_utilizado <= ia_max else st.error("❌ Índice de Aproveitamento EXCEDE o permitido")
    if tp_min is not None:
        st.success("✅ Taxa de Permeabilidade atende o mínimo") if tp_prevista >= tp_min else st.warning("⚠️ Taxa de Permeabilidade abaixo do mínimo exigido.")
