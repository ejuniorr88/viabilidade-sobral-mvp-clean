from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from shapely.geometry import shape, Point
from shapely.ops import transform
from shapely.strtree import STRtree
from pyproj import Transformer

DATA_DIR = Path("data")
RUAS_FILE = DATA_DIR / "ruas.json"

# Lat/Lon -> WebMercator (meters)
point = Point(lon, lat)

@dataclass(frozen=True)
class StreetHit:
    name: str
    street_type: Optional[str]
    distance_m: float

def _infer_name(props: Dict[str, Any]) -> str:
    for k in ("nome", "name", "logradouro", "rua", "via"):
        v = props.get(k)
        if v:
            return str(v)
    return "Via (sem nome)"

def _infer_type(props: Dict[str, Any]) -> Optional[str]:
    for k in ("tipo", "type", "categoria", "class", "highway"):
        v = props.get(k)
        if v:
            return str(v)
    return None

def _looks_lonlat(bounds_list: List[Tuple[float, float, float, float]]) -> bool:
    if not bounds_list:
        return True
    for minx, miny, maxx, maxy in bounds_list:
        if any(math.isnan(v) for v in (minx, miny, maxx, maxy)):
            continue
        if not (-180 <= minx <= 180 and -180 <= maxx <= 180 and -90 <= miny <= 90 and -90 <= maxy <= 90):
            return False
    return True

class StreetsIndex:
    def __init__(self, features: List[Dict[str, Any]]):
        self._features = features
        self._geoms = [f["_geom"] for f in features]
        self._tree = STRtree(self._geoms)

    @staticmethod
    def load(path: Path = RUAS_FILE) -> "StreetsIndex":
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")

        gj = json.loads(path.read_text(encoding="utf-8"))
        feats = gj.get("features") or []
        if not feats:
            return StreetsIndex([])

        sample_bounds: List[Tuple[float, float, float, float]] = []
        for f in feats[:20]:
            try:
                g = shape(f.get("geometry"))
                sample_bounds.append(g.bounds)
            except Exception:
                continue

        lonlat = _looks_lonlat(sample_bounds)

        out: List[Dict[str, Any]] = []
        for f in feats:
            geom = f.get("geometry")
            if not geom:
                continue
            try:
                g = shape(geom)
            except Exception:
                continue

            props = f.get("properties") or {}
            name = _infer_name(props)
            stype = _infer_type(props)

            g_m = transform(_TO_3857.transform, g) if lonlat else g

            out.append({"_geom": g_m, "name": name, "type": stype})

        return StreetsIndex(out)

    def nearest_street(self, lon: float, lat: float, radius_m: float) -> Optional[StreetHit]:
        if not self._features:
            return None

        p_m = Point(*_TO_3857.transform(lon, lat))
        candidates = self._tree.query(p_m.buffer(radius_m))
        if not candidates:
            return None

        best_d = None
        best_feat = None

        # map geom object id -> index for speed
        geom_id_to_idx = {id(g): i for i, g in enumerate(self._geoms)}

        for g in candidates:
            try:
                d = float(g.distance(p_m))
            except Exception:
                continue
            if d <= radius_m and (best_d is None or d < best_d):
                best_d = d
                best_feat = self._features[geom_id_to_idx[id(g)]]

        if best_d is None or best_feat is None:
            return None

        return StreetHit(name=str(best_feat["name"]), street_type=best_feat.get("type"), distance_m=best_d)

_INDEX: Optional[StreetsIndex] = None

def get_streets_index() -> StreetsIndex:
    global _INDEX
    if _INDEX is None:
        _INDEX = StreetsIndex.load()
    return _INDEX

def find_street(lon: float, lat: float, radius_m: float = 100.0) -> Tuple[Optional[str], Optional[str], Optional[float]]:
    idx = get_streets_index()
    hit = idx.nearest_street(lon, lat, radius_m)
    if not hit:
        return None, None, None
    return hit.name, hit.street_type, hit.distance_m
