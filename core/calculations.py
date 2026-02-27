from __future__ import annotations

from typing import Any, Dict, Optional


def _safe_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return float(v)
    except Exception:
        return None


def _rule_get(rule: Any, key: str) -> Any:
    """Tenta ler como dict e como objeto (dataclass)."""
    if rule is None:
        return None
    try:
        return rule.get(key)  # type: ignore[attr-defined]
    except Exception:
        return getattr(rule, key, None)


def _pick_first(rule: Any, *keys: str) -> Optional[float]:
    for k in keys:
        v = _safe_float(_rule_get(rule, k))
        if v is not None:
            return v
    return None


def compute(
    *,
    # nomes "novos" (pt)
    area_lote_m2: Optional[float] = None,
    testada_m: Optional[float] = None,
    profundidade_m: Optional[float] = None,
    area_terreo_m2: float = 0.0,
    zone_rule: Any = None,
    # compat: nomes "antigos" / diferentes (en)
    lot_area_m2: Optional[float] = None,
    frontage_m: Optional[float] = None,
    depth_m: Optional[float] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Calcula TO/TP/IA e checks básicos.

    Compatibilidade:
      - aceita area_lote_m2 OU lot_area_m2
      - aceita testada_m/frontage_m
      - aceita profundidade_m/depth_m
      - aceita zone_rule como dict, dataclass (ZoneRule) ou objeto com atributos
    """

    # Normaliza entradas (prioridade: pt -> en)
    area_lote = _safe_float(area_lote_m2)
    if area_lote is None:
        area_lote = _safe_float(lot_area_m2)

    testada = _safe_float(testada_m)
    if testada is None:
        testada = _safe_float(frontage_m)

    profundidade = _safe_float(profundidade_m)
    if profundidade is None:
        profundidade = _safe_float(depth_m)

    area_terreo = float(area_terreo_m2 or 0.0)

    if not area_lote or area_lote <= 0:
        raise ValueError("Área do lote (m²) inválida.")

    # Lê regras (suporta nomes antigos e novos)
    to_max = _pick_first(zone_rule, "to_max_pct", "to_max", "to_sub_max", "to", "taxa_ocupacao_max")
    tp_min = _pick_first(zone_rule, "tp_min_pct", "tp_min", "tp", "taxa_permeabilidade_min")
    ia_max = _pick_first(zone_rule, "ia_max", "ia", "indice_aproveitamento_max")

    recuo_frontal = _pick_first(zone_rule, "recuo_frontal_m", "recuo_frontal", "setback_front_m")
    recuo_lateral = _pick_first(zone_rule, "recuo_lateral_m", "recuo_lateral", "setback_side_m")
    recuo_fundos = _pick_first(zone_rule, "recuo_fundos_m", "recuo_fundos", "setback_back_m")

    # Cálculos
    to_utilizada = area_terreo / area_lote
    area_permeavel_min = (tp_min or 0.0) * area_lote if tp_min is not None else None
    area_max_total = (ia_max or 0.0) * area_lote if ia_max is not None else None

    out: Dict[str, Any] = {
        "inputs": {
            "area_lote_m2": area_lote,
            "testada_m": testada,
            "profundidade_m": profundidade,
            "area_terreo_m2": area_terreo,
        },
        "rules": {
            "to_max": to_max,
            "tp_min": tp_min,
            "ia_max": ia_max,
            "recuo_frontal_m": recuo_frontal,
            "recuo_lateral_m": recuo_lateral,
            "recuo_fundos_m": recuo_fundos,
        },
        "calc": {
            "to_utilizada": to_utilizada,
            "to_ok": (to_max is None) or (to_utilizada <= to_max),
            "area_permeavel_min_m2": area_permeavel_min,
            "area_max_total_m2": area_max_total,
        },
    }

    # Checks de coerência geométrica (se tiver testada/profundidade)
    if testada and profundidade and testada > 0 and profundidade > 0:
        out["calc"]["area_retangular_m2"] = testada * profundidade
        out["calc"]["area_lote_vs_retangulo_ratio"] = area_lote / (testada * profundidade)

    return out
