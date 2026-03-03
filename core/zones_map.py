from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from shapely.geometry import Point, shape
from shapely.prepared import prep


@dataclass(frozen=True)
class ZoneFeature:
    sigla: str
    geom_prep: Any  # PreparedGeometry


def load_zones(zone_file: Path) -> List[ZoneFeature]:
    obj = json.loads(zone_file.read_text(encoding="utf-8"))

    feats = obj.get("features") if isinstance(obj, dict) else None
    if not feats:
        raise RuntimeError("zoneamento_light.json inválido: não achei 'features'.")

    out: List[ZoneFeature] = []
    for f in feats:
        props = f.get("properties") or {}
        sigla = props.get("sigla") or props.get("SIGLA") or props.get("zona")
        if not sigla:
            continue
        geom = f.get("geometry")
        if not geom:
            continue
        out.append(ZoneFeature(sigla=str(sigla).strip(), geom_prep=prep(shape(geom))))

    if not out:
        raise RuntimeError("Nenhuma zona encontrada no GeoJSON.")

    return out


def zone_from_latlon(zones: List[ZoneFeature], lat: float, lon: float) -> Optional[str]:
    p = Point(float(lon), float(lat))
    for z in zones:
        if z.geom_prep.contains(p):
            return z.sigla
    return None
