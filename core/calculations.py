from __future__ import annotations

"""Cálculos (TO / TP / IA) para o MVP.

IMPORTANTE: o `app.py` deste repositório usa `core.calculations.compute(...)`
E espera um dicionário com as chaves abaixo:

- to_max_pct, tp_min_pct, ia_max
- to_max_m2,  tp_min_m2,  ia_max_m2
- option_standard / option_art112

Esta implementação é tolerante a diferentes nomes vindos do Supabase.
"""

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
    if rule is None:
        return None
    if isinstance(rule, dict):
        return rule.get(key)
    return getattr(rule, key, None)


def _pick_first(rule: Any, *keys: str) -> Optional[float]:
    for k in keys:
        v = _safe_float(_rule_get(rule, k))
        if v is not None:
            return v
    return None


def _pct_to_fraction(v: Optional[float]) -> Optional[float]:
    """Normaliza valores que podem vir como 0.6 ou 60."""
    if v is None:
        return None
    return v / 100.0 if v > 1.5 else v


def _area_buildable(
    *,
    testada_m: Optional[float],
    profundidade_m: Optional[float],
    recuo_frontal_m: float,
    recuo_fundos_m: float,
    recuo_lateral_left_m: float,
    recuo_lateral_right_m: float,
) -> float:
    if not testada_m or not profundidade_m:
        return 0.0
    w = max(0.0, float(testada_m) - float(recuo_lateral_left_m) - float(recuo_lateral_right_m))
    d = max(0.0, float(profundidade_m) - float(recuo_frontal_m) - float(recuo_fundos_m))
    return w * d


def compute(
    *,
    # nomes "novos" (pt)
    area_lote_m2: Optional[float] = None,
    testada_m: Optional[float] = None,
    profundidade_m: Optional[float] = None,
    area_terreo_m2: float = 0.0,
    zone_rule: Any = None,
    # compatibilidade com chamadas antigas
    lot_area_m2: Optional[float] = None,
    frontage_m: Optional[float] = None,
    depth_m: Optional[float] = None,
    ground_area_m2: Optional[float] = None,
    largura_m: Optional[float] = None,
    rule: Any = None,
    **_: Any,
) -> Dict[str, Any]:
    """Computa TO/TP/IA + opções de envelope.

    O retorno é "flat" para casar com o uso no `app.py`.
    """

    area_lote = _safe_float(area_lote_m2)
    if area_lote is None:
        area_lote = _safe_float(lot_area_m2)
    if area_lote is None or area_lote <= 0:
        raise ValueError("Área do lote (m²) inválida.")

    testada = _safe_float(testada_m)
    if testada is None:
        testada = _safe_float(frontage_m)
    if testada is None:
        testada = _safe_float(largura_m)

    profundidade = _safe_float(profundidade_m)
    if profundidade is None:
        profundidade = _safe_float(depth_m)

    if zone_rule is None and rule is not None:
        zone_rule = rule

    if ground_area_m2 is not None and (area_terreo_m2 in (None, 0.0)):
        area_terreo_m2 = float(ground_area_m2)

    area_terreo = float(area_terreo_m2 or 0.0)

    # Índices (tolerante a nomes diferentes)
    to_raw = _pick_first(zone_rule, "to_max_pct", "to_max", "to_sub_max", "to", "taxa_ocupacao_max")
    tp_raw = _pick_first(zone_rule, "tp_min_pct", "tp_min", "tp", "taxa_permeabilidade_min")
    ia_max = _pick_first(zone_rule, "ia_max", "ia", "indice_aproveitamento_max")

    to_frac = _pct_to_fraction(to_raw) or 0.0
    tp_frac = _pct_to_fraction(tp_raw) or 0.0
    ia_val = float(ia_max or 0.0)

    to_max_m2 = float(area_lote) * to_frac
    tp_min_m2 = float(area_lote) * tp_frac
    ia_max_m2 = float(area_lote) * ia_val

    # Recuos (padrão 0 se não tiver)
    recuo_frontal = _pick_first(zone_rule, "recuo_frontal_m", "recuo_frontal", "setback_front_m") or 0.0
    recuo_lateral = _pick_first(zone_rule, "recuo_lateral_m", "recuo_lateral", "setback_side_m") or 0.0
    recuo_fundos = _pick_first(zone_rule, "recuo_fundos_m", "recuo_fundos", "setback_back_m") or 0.0

    allow_attach_one_side = bool(_rule_get(zone_rule, "allow_attach_one_side") or False)

    # Envelope padrão
    buildable_standard = _area_buildable(
        testada_m=testada,
        profundidade_m=profundidade,
        recuo_frontal_m=recuo_frontal,
        recuo_fundos_m=recuo_fundos,
        recuo_lateral_left_m=recuo_lateral,
        recuo_lateral_right_m=recuo_lateral,
    )
    max_terreo_standard = min(to_max_m2, buildable_standard)

    # Art.112 (encostar em 1 lateral)
    buildable_art112 = _area_buildable(
        testada_m=testada,
        profundidade_m=profundidade,
        recuo_frontal_m=recuo_frontal,
        recuo_fundos_m=recuo_fundos,
        recuo_lateral_left_m=0.0 if allow_attach_one_side else recuo_lateral,
        recuo_lateral_right_m=recuo_lateral,
    )
    max_terreo_art112 = min(to_max_m2, buildable_art112)

    return {
        "to_max_pct": to_frac * 100.0,
        "tp_min_pct": tp_frac * 100.0,
        "ia_max": ia_val,
        "to_max_m2": float(to_max_m2),
        "tp_min_m2": float(tp_min_m2),
        "ia_max_m2": float(ia_max_m2),
        "option_standard": {
            "Área máxima pelo envelope de recuos (m²)": float(buildable_standard),
            "Máximo no térreo (respeitando TO e recuos) (m²)": float(max_terreo_standard),
        },
        "option_art112": {
            "Área máxima pelo envelope (Art.112) (m²)": float(buildable_art112),
            "Máximo no térreo (Art.112, respeitando TO) (m²)": float(max_terreo_art112),
        },
        "checks": {
            "to_ok": bool(area_terreo <= to_max_m2 + 1e-9),
        },
    }
