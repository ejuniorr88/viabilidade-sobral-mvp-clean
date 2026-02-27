from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from shapely.geometry import Point, shape
from shapely.ops import transform
from shapely.strtree import STRtree
from pyproj import Transformer

DATA_DIR = Path("data")
RUAS_FILE = DATA_DIR / "ruas.json"


@dataclass(frozen=True)
class StreetHit:
    name: str
    street_type: Optional[str]
    distance_m: float


def _infer_name(props: Dict[str, Any]) -> str:
    for k in ("nome", "name", "logradouro", "rua", "via", "log_ofic"):
        v = props.get(k)
        if v:
            return str(v)
    return "Via (sem nome)"


def _infer_type(props: Dict[str, Any]) -> Optional[str]:
    for k in ("tipo", "type", "categoria", "class", "highway", "hierarquia"):
        v = props.get(k)
        if v:
            return str(v)
    return None


class StreetsIndex:
    def __init__(self) -> None:
        self._tree: Optional[STRtree] = None
        self._geoms: List[Any] = []
        self._props: List[Dict[str, Any]] = []
        self._wgs84_to_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

    def load(self) -> None:
        if self._tree is not None:
            return

        if not RUAS_FILE.exists():
            self._tree = STRtree([])
            return

        data = json.loads(RUAS_FILE.read_text(encoding="utf-8"))
        feats = data.get("features", [])

        geoms: List[Any] = []
        props_list: List[Dict[str, Any]] = []

        for f in feats:
            g = f.get("geometry")
            if not g:
                continue
            try:
                geom = shape(g)
            except Exception:
                continue

            props = f.get("properties", {}) or {}
            geom_m = transform(self._wgs84_to_3857.transform, geom)
            geoms.append(geom_m)
            props_list.append(props)

        self._geoms = geoms
        self._props = props_list
        self._tree = STRtree(self._geoms)

    def nearest_street(self, lat: float, lon: float, radius_m: float = 500.0) -> Optional[StreetHit]:
        self.load()
        if not self._tree or not self._geoms:
            return None

        p = transform(self._wgs84_to_3857.transform, Point(float(lon), float(lat)))

        cand = self._tree.query(p.buffer(float(radius_m)))
        if not cand:
            return None

        best_idx: Optional[int] = None
        best_dist = float("inf")

        # STRtree retorna geoms; achamos o índice na lista original
        for geom in cand:
            try:
                idx = self._geoms.index(geom)
            except ValueError:
                continue
            d = p.distance(geom)
            if d < best_dist:
                best_dist = d
                best_idx = idx

        if best_idx is None or best_dist > float(radius_m):
            return None

        props = self._props[best_idx]
        return StreetHit(
            name=_infer_name(props),
            street_type=_infer_type(props),
            distance_m=float(best_dist),
        )


_INDEX: Optional[StreetsIndex] = None


def get_streets_index() -> StreetsIndex:
    global _INDEX
    if _INDEX is None:
        _INDEX = StreetsIndex()
    return _INDEX


def find_street(lat: float, lon: float, radius_m: float = 500.0) -> Optional[Dict[str, Any]]:
    hit = get_streets_index().nearest_street(lat=lat, lon=lon, radius_m=radius_m)
    if not hit:
        return None
    return {"name": hit.name, "type": hit.street_type, "distance_m": hit.distance_m}
