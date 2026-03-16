from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from shapely.geometry import Point, shape
from shapely.prepared import prep

from core.zone_resolution import resolve_zone_from_feature_properties


@dataclass(frozen=True)
class ZoneFeature:
    geom: Any
    geom_prep: Any
    props: Dict[str, Any]
    zone_sigla: str
    subzone_code: str
    display_label: str
    raw_sigla: str
    raw_subzona: str
    zona_sigla_text: str


def load_zones(zone_file: Path) -> List[ZoneFeature]:
    obj = json.loads(zone_file.read_text(encoding="utf-8"))
    feats = obj.get("features") if isinstance(obj, dict) else None
    if not feats:
        raise RuntimeError("zoneamento_light.json inválido: não achei 'features'.")

    out: List[ZoneFeature] = []
    for f in feats:
        props = dict(f.get("properties") or {})
        geom = f.get("geometry")
        if not geom:
            continue
        try:
            g = shape(geom)
        except Exception:
            continue
        try:
            res = resolve_zone_from_feature_properties(props)
        except Exception:
            continue
        if not res.zone_sigla_db:
            continue
        out.append(
            ZoneFeature(
                geom=g,
                geom_prep=prep(g),
                props=props,
                zone_sigla=res.zone_sigla_db,
                subzone_code=res.subzone_code_db or "PADRAO",
                display_label=res.display_label,
                raw_sigla=res.zone_sigla_raw,
                raw_subzona=res.subzone_raw,
                zona_sigla_text=str(props.get("zona_sigla") or props.get("ZONA_SIGLA") or "").strip(),
            )
        )

    if not out:
        raise RuntimeError("Nenhuma zona encontrada no GeoJSON.")
    return out


def _as_info(z: ZoneFeature) -> Dict[str, str]:
    return {
        "zone_sigla": z.zone_sigla,
        "subzone_code": z.subzone_code,
        "display_label": z.display_label,
        "raw_sigla": z.raw_sigla,
        "raw_subzona": z.raw_subzona,
        "zona_sigla_text": z.zona_sigla_text,
    }


def zone_info_from_latlon(zones: List[ZoneFeature], lat: float, lon: float) -> Optional[Dict[str, str]]:
    p = Point(float(lon), float(lat))

    # caminho principal
    for z in zones:
        try:
            if z.geom_prep.covers(p):
                return _as_info(z)
        except Exception:
            try:
                if z.geom.covers(p):
                    return _as_info(z)
            except Exception:
                continue

    # fallback por distância curta para borda/buracos pequenos
    best: Optional[ZoneFeature] = None
    best_dist: Optional[float] = None
    for z in zones:
        try:
            d = float(z.geom.distance(p))
        except Exception:
            continue
        if best_dist is None or d < best_dist:
            best_dist = d
            best = z

    if best is not None and best_dist is not None and best_dist <= 0.0002:
        return _as_info(best)
    return None


def zone_from_latlon(zones: List[ZoneFeature], lat: float, lon: float) -> Optional[str]:
    info = zone_info_from_latlon(zones, lat, lon)
    return info["zone_sigla"] if info else None
