from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st


def _to_float_ptbr(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s:
        return None
    # remove milhares e trocar vírgula por ponto
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None


def _pct(num: float, den: float) -> float:
    if den <= 0:
        return 0.0
    return (num / den) * 100.0


def _get_rule_pct(rule: Dict[str, Any], key_pct: str, key_frac: str) -> Optional[float]:
    """
    Normaliza regra em percentual (0-100).
    - Se existir *_pct usa direto.
    - Senão, se existir versão fração (0-1) converte *100.
    """
    if not rule:
        return None
    v_pct = rule.get(key_pct)
    if v_pct is not None and v_pct != "":
        try:
            return float(v_pct)
        except Exception:
            pass
    v_frac = rule.get(key_frac)
    if v_frac is not None and v_frac != "":
        try:
            return float(v_frac) * 100.0
        except Exception:
            pass
    return None


def compute_indices_for_report(*, calc: Dict[str, Any], lote: Dict[str, Any]) -> None:
    """
    Calcula e grava no calc todos os números necessários para:
    - Seção 5 (Análise)
    - Seção 6 (Relatório leigo)

    Regra importante (preservando comportamento do seu UI):
    - Se "Área pretendida no térreo" == 0 (ou vazio),
      o sistema assume automaticamente o *máximo permitido* (Opção 2 / Art.112),
      limitado por TO e recuo de fundo.
    """
    rule = (calc.get("rule") or {}) if isinstance(calc.get("rule"), dict) else {}

    # inputs lote
    A = _to_float_ptbr(lote.get("area_lote_m2") or lote.get("area_lote") or lote.get("area"))
    W = _to_float_ptbr(lote.get("testada_m") or lote.get("testada") or lote.get("largura_m"))
    D = _to_float_ptbr(lote.get("profundidade_m") or lote.get("profundidade") or lote.get("comprimento_m"))
    A_terreo_in = _to_float_ptbr(lote.get("area_terreo_m2") or lote.get("area_terreo") or lote.get("area_terreo_input"))

    if not A or A <= 0:
        calc["err"] = "Área do lote inválida."
        return
    if not W or not D or W <= 0 or D <= 0:
        calc["err"] = "Testada e profundidade são necessárias para o relatório."
        return

    # regra (pct)
    to_max_pct = _get_rule_pct(rule, "to_max_pct", "to_max")
    tp_min_pct = _get_rule_pct(rule, "tp_min_pct", "tp_min")
    ia_max = rule.get("ia_max")
    try:
        ia_max = float(ia_max) if ia_max is not None and ia_max != "" else None
    except Exception:
        ia_max = None

    # recuos
    rf = _to_float_ptbr(rule.get("recuo_frontal_m")) or 0.0
    rl = _to_float_ptbr(rule.get("recuo_lateral_m")) or 0.0
    rfd = _to_float_ptbr(rule.get("recuo_fundos_m")) or 0.0

    # ---------
    # 1) Limite por TO
    # ---------
    A_to = None
    if to_max_pct is not None:
        A_to = A * (to_max_pct / 100.0)

    # ---------
    # Opção 1: recuos padrão
    # ---------
    W_util = max(0.0, W - 2.0 * rl)
    D_util = max(0.0, D - rf - rfd)
    A_recuos = W_util * D_util
    A_op1 = min(A_to, A_recuos) if A_to is not None else A_recuos

    # ---------
    # Opção 2: Art.112 (zerar frontal + laterais; fundo obrigatório)
    # ---------
    W_util2 = W
    D_util2 = max(0.0, D - rfd)
    A_recuos2 = W_util2 * D_util2
    A_op2 = min(A_to, A_recuos2) if A_to is not None else A_recuos2

    # ---------
    # Térreo adotado (para a seção 5):
    # Se input == 0 -> assumir máximo permitido (Opção 2)
    # ---------
    if A_terreo_in is None or A_terreo_in <= 0:
        A_terreo_adot = A_op2
        calc["assumiu_terreo_maximo"] = True
    else:
        A_terreo_adot = float(A_terreo_in)
        calc["assumiu_terreo_maximo"] = False

    # TP mínima (m²) e "máximo impermeável" em cada cenário
    A_perm_min = None
    if tp_min_pct is not None:
        A_perm_min = A * (tp_min_pct / 100.0)

    def _tp_scenario(A_terreo: float):
        A_livre = A - A_terreo
        if A_perm_min is None:
            return {"area_livre_m2": A_livre, "area_perm_min_m2": None, "area_imperm_max_m2": None}
        return {
            "area_livre_m2": A_livre,
            "area_perm_min_m2": A_perm_min,
            "area_imperm_max_m2": A_livre - A_perm_min,
        }

    tp_op1 = _tp_scenario(A_op1)
    tp_op2 = _tp_scenario(A_op2)

    # IA/TO "utilizados" (considerando térreo adotado como proxy)
    to_util_pct = _pct(A_terreo_adot, A)
    ia_util = (A_terreo_adot / A) if A > 0 else 0.0

    # TP prevista (%): se usuário não informou nada, mostrar a mínima exigida (e não 100%)
    tp_prevista_pct = None
    if tp_min_pct is not None:
        tp_prevista_pct = float(tp_min_pct)

    # Guardar no calc (contrato para relatório)
    calc["report"] = {
        "area_lote_m2": A,
        "testada_m": W,
        "profundidade_m": D,
        "to_max_pct": to_max_pct,
        "tp_min_pct": tp_min_pct,
        "ia_max": ia_max,
        "recuo_frontal_m": rf,
        "recuo_lateral_m": rl,
        "recuo_fundos_m": rfd,
        "area_max_to_m2": A_to,
        "op1": {"area_max_recuos_m2": A_recuos, "area_terreo_max_m2": A_op1, **tp_op1},
        "op2": {"area_max_recuos_m2": A_recuos2, "area_terreo_max_m2": A_op2, **tp_op2},
        "area_terreo_adotada_m2": A_terreo_adot,
    }

    calc["ia_utilizado"] = ia_util
    calc["to_utilizada_pct"] = to_util_pct
    calc["tp_prevista_pct"] = tp_prevista_pct


def render_analise_section(*, calc: Dict[str, Any], lote: Dict[str, Any]) -> None:
    st.header("5) Análise Urbanística")

    # Recalcular aqui para garantir que números existem mesmo quando relatório precisa
    compute_indices_for_report(calc=calc, lote=lote)

    ia = calc.get("ia_utilizado")
    to_pct = calc.get("to_utilizada_pct")
    tp_pct = calc.get("tp_prevista_pct")

    st.write(f"IA utilizado (considerando térreo adotado): {ia:.2f}" if isinstance(ia, (int, float)) else "IA utilizado: —")
    st.write(f"TO utilizada: {to_pct:.1f}%" if isinstance(to_pct, (int, float)) else "TO utilizada: —")
    st.write(f"TP prevista: {tp_pct:.1f}%" if isinstance(tp_pct, (int, float)) else "TP prevista: —")

    if calc.get("assumiu_terreo_maximo"):
        st.caption("Obs.: Como a área pretendida no térreo foi 0, o sistema assumiu automaticamente o máximo permitido (Opção 2 / Art.112).")
