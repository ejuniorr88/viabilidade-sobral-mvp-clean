from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CalcResult:
    to_max_area: float
    tp_min_area: float
    ia_max_area_total: float

    buildable_area_standard: float
    max_terreo_standard: float

    buildable_area_art112: float
    max_terreo_art112: float


def clamp0(x: float) -> float:
    return x if x > 0 else 0.0


def compute(
    lot_area_m2: float,
    lot_width_m: float,
    lot_depth_m: float,
    to_max_pct: float,
    tp_min_pct: float,
    ia_max: float,
    recuo_frontal_m: float,
    recuo_lateral_m: float,
    recuo_fundos_m: float,
) -> CalcResult:
    lot_area_m2 = float(lot_area_m2)
    lot_width_m = float(lot_width_m)
    lot_depth_m = float(lot_depth_m)

    to_max_area = lot_area_m2 * (float(to_max_pct) / 100.0)
    tp_min_area = lot_area_m2 * (float(tp_min_pct) / 100.0)
    ia_max_area_total = lot_area_m2 * float(ia_max)

    # Opção 1: recuos padrão
    bw = clamp0(lot_width_m - 2.0 * float(recuo_lateral_m))
    bd = clamp0(lot_depth_m - float(recuo_frontal_m) - float(recuo_fundos_m))
    buildable_standard = bw * bd
    max_terreo_standard = min(to_max_area, buildable_standard)

    # Opção 2: Art. 112 (zerar frontal e laterais, manter fundos)
    bw2 = clamp0(lot_width_m)
    bd2 = clamp0(lot_depth_m - float(recuo_fundos_m))
    buildable_art112 = bw2 * bd2
    max_terreo_art112 = min(to_max_area, buildable_art112)

    return CalcResult(
        to_max_area=to_max_area,
        tp_min_area=tp_min_area,
        ia_max_area_total=ia_max_area_total,
        buildable_area_standard=buildable_standard,
        max_terreo_standard=max_terreo_standard,
        buildable_area_art112=buildable_art112,
        max_terreo_art112=max_terreo_art112,
    )
