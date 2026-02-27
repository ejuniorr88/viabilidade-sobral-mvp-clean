from __future__ import annotations

from typing import Any, Dict, Optional


def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None or x == "":
            return None
        return float(x)
    except Exception:
        return None


def _rule_get(rule: Any, key: str) -> Any:
    """Read rule value from dict-like OR attribute-like objects."""
    if rule is None:
        return None
    if hasattr(rule, "get"):
        try:
            v = rule.get(key)
            if v is not None:
                return v
        except Exception:
            pass
    return getattr(rule, key, None)


def _pick_first(rule: Any, *keys: str) -> Optional[float]:
    for k in keys:
        v = _safe_float(_rule_get(rule, k))
        if v is not None:
            return v
    return None


def compute(
    *,
    area_lote_m2: float,
    testada_m: Optional[float] = None,
    largura_m: Optional[float] = None,   # compatibilidade
    profundidade_m: Optional[float] = None,
    area_terreo_m2: float = 0.0,
    zone_rule: Any = None,
) -> Dict[str, Any]:
    """Calcula TO / TP / IA e checks básicos.

    Compatível com chamadas antigas e novas:
    - aceita `testada_m=` (novo) e `largura_m=` (antigo).
    - `zone_rule` pode ser dict, ZoneRule(dict-like) ou objeto com atributos.
    """

    largura_real = testada_m if (testada_m not in (None, 0)) else largura_m

    to_max = _pick_first(zone_rule, "to_max_pct", "to_max", "to", "taxa_ocupacao_max")
    tp_min = _pick_first(zone_rule, "tp_min_pct", "tp_min", "tp", "taxa_permeabilidade_min")
    ia_max = _pick_first(zone_rule, "ia_max", "ia", "indice_aproveitamento_max")

    recuo_frontal = _pick_first(zone_rule, "recuo_frontal_m", "setback_front_m")
    recuo_lateral = _pick_first(zone_rule, "recuo_lateral_m", "setback_side_m")
    recuo_fundos = _pick_first(zone_rule, "recuo_fundos_m", "setback_back_m")

    max_area_ocupada = (area_lote_m2 * to_max) if to_max is not None else None
    min_area_permeavel = (area_lote_m2 * tp_min) if tp_min is not None else None
    max_area_total = (area_lote_m2 * ia_max) if ia_max is not None else None

    ok_to = None
    if max_area_ocupada is not None:
        ok_to = float(area_terreo_m2) <= float(max_area_ocupada) + 1e-9

    return {
        "inputs": {
            "area_lote_m2": float(area_lote_m2),
            "testada_m": None if largura_real is None else float(largura_real),
            "profundidade_m": None if profundidade_m is None else float(profundidade_m),
            "area_terreo_m2": float(area_terreo_m2),
        },
        "indices": {
            "to_max": to_max,
            "tp_min": tp_min,
            "ia_max": ia_max,
        },
        "recuos": {
            "recuo_frontal_m": recuo_frontal,
            "recuo_lateral_m": recuo_lateral,
            "recuo_fundos_m": recuo_fundos,
        },
        "areas": {
            "max_area_ocupada_m2": max_area_ocupada,
            "min_area_permeavel_m2": min_area_permeavel,
            "max_area_total_m2": max_area_total,
        },
        "checks": {
            "to_ok": ok_to,
            "tp_ok": None,
            "ia_ok": None,
        },
    }
