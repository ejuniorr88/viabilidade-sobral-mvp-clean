from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .zone_resolution import resolve_zone_from_feature_properties

from shapely.geometry import Point, shape
from shapely.prepared import prep


@dataclass(frozen=True)
class ZoneFeature:
    sigla: str
    props: Dict[str, Any]
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
        # ZEIS: o GeoJSON traz 'sigla'='ZEIS' e 'subzona'='ZEIS 1/2/3'.
        # Para permitir parâmetros diferentes por setor, usamos 'subzona' quando existir.
        if str(sigla).strip().upper() == "ZEIS":
            sub = props.get("subzona") or props.get("SUBZONA")
            if sub:
                sigla = sub
        if not sigla:
            continue
        geom = f.get("geometry")
        if not geom:
            continue
        out.append(ZoneFeature(sigla=str(sigla).strip(), props=props, geom_prep=prep(shape(geom))))

    if not out:
        raise RuntimeError("Nenhuma zona encontrada no GeoJSON.")

    return out




def zone_info_from_latlon(zones: List[ZoneFeature], lat: float, lon: float) -> Optional[Dict[str, Any]]:
    p = Point(float(lon), float(lat))
    for z in zones:
        if z.geom_prep.contains(p):
            res = resolve_zone_from_feature_properties(z.props)
            out = res.as_dict()
            out["feature_sigla"] = z.sigla
            out["feature_properties"] = z.props
            return out
    return None


def zone_from_latlon(zones: List[ZoneFeature], lat: float, lon: float) -> Optional[str]:
    info = zone_info_from_latlon(zones, lat, lon)
    if not info:
        return None
    return info.get("display_label") or info.get("zone_sigla_db") or info.get("zone_sigla_raw")
