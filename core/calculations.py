from __future__ import annotations

from typing import Any, Dict, Optional


def _safe_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        if isinstance(v, bool):
            return float(int(v))
        return float(v)
    except Exception:
        return None


def _first(*vals: Any) -> Optional[float]:
    for v in vals:
        fv = _safe_float(v)
        if fv is not None:
            return fv
    return None


def compute(
    *,
    # aceita nomes antigos e novos (o app chama lot_area_m2)
    lot_area_m2: float = 0.0,
    area_lote_m2: Optional[float] = None,
    testada_m: Optional[float] = None,
    largura_m: Optional[float] = None,   # compat
    profundidade_m: Optional[float] = None,
    built_ground_m2: float = 0.0,
    area_terreo_m2: Optional[float] = None,  # compat
    # parâmetros vindo do app/supabase
    to_max_pct: Optional[float] = None,
    tp_min_pct: Optional[float] = None,
    ia_max: Optional[float] = None,
    recuo_frontal_m: Optional[float] = None,
    recuo_lateral_m: Optional[float] = None,
    recuo_fundos_m: Optional[float] = None,
    allow_attach_one_side: bool = False,
) -> Dict[str, Any]:
    """Calcula TO/TP/IA + envelope básico.

    Retorna chaves esperadas pelo app:
    - to_max_pct, tp_min_pct, ia_max
    - to_max_m2, tp_min_m2, ia_max_m2
    - option_standard / option_art112
    """

    lot_area = _first(lot_area_m2, area_lote_m2, 0.0) or 0.0
    largura = _first(testada_m, largura_m, 0.0) or 0.0
    prof = _first(profundidade_m, 0.0) or 0.0
    terreo = _first(built_ground_m2, area_terreo_m2, 0.0) or 0.0

    # Normaliza % e IA
    to_pct = _first(to_max_pct, 0.0) or 0.0
    tp_pct = _first(tp_min_pct, 0.0) or 0.0
    ia = _first(ia_max, 0.0) or 0.0

    # Se vierem em formato 0-100 (percentual), converte para fração
    if to_pct > 1.0:
        to_pct = to_pct / 100.0
    if tp_pct > 1.0:
        tp_pct = tp_pct / 100.0

    to_max_m2 = lot_area * to_pct
    tp_min_m2 = lot_area * tp_pct
    ia_max_m2 = lot_area * ia

    # Envelope simples (retângulo do lote menos recuos)
    rf = _first(recuo_frontal_m, 0.0) or 0.0
    rl = _first(recuo_lateral_m, 0.0) or 0.0
    rb = _first(recuo_fundos_m, 0.0) or 0.0

    def _envelope_area(front: float, side: float, back: float) -> float:
        w = max(largura - (0.0 if allow_attach_one_side else side * 2.0), 0.0)
        # se pode encostar em 1 lateral, subtrai só 1 lateral
        if allow_attach_one_side:
            w = max(largura - side, 0.0)
        d = max(prof - front - back, 0.0)
        return w * d

    env_std = _envelope_area(rf, rl, rb)

    # Art.112: zera frontal e laterais, mantém fundos
    env_112 = _envelope_area(0.0, 0.0, rb)

    # Máximo no térreo respeitando TO (se TO = 0, fica 0)
    max_terreo_std = min(env_std, to_max_m2) if to_max_m2 > 0 else 0.0
    max_terreo_112 = min(env_112, to_max_m2) if to_max_m2 > 0 else 0.0

    return {
        "to_max_pct": to_pct * 100.0,
        "tp_min_pct": tp_pct * 100.0,
        "ia_max": ia,
        "to_max_m2": float(to_max_m2),
        "tp_min_m2": float(tp_min_m2),
        "ia_max_m2": float(ia_max_m2),
        "option_standard": {
            "Área máxima pelo envelope de recuos (m²)": float(env_std),
            "Máximo no térreo (respeitando TO e recuos) (m²)": float(max_terreo_std),
        },
        "option_art112": {
            "Área máxima pelo envelope (Art.112) (m²)": float(env_112),
            "Máximo no térreo (Art.112, respeitando TO) (m²)": float(max_terreo_112),
        },
        "inputs": {
            "lot_area_m2": lot_area,
            "testada_m": largura,
            "profundidade_m": prof,
            "built_ground_m2": terreo,
        },
        "checks": {
            "terreo_ok_to": (terreo <= to_max_m2) if to_max_m2 > 0 else None,
            "terreo_ok_envelope_std": (terreo <= env_std) if env_std > 0 else None,
        },
    }
