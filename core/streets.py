from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from shapely.geometry import shape, Point
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


class StreetsIndex:
    def __init__(self, ruas_path: Path = RUAS_FILE):
        self.ruas_path = ruas_path
        self._loaded = False
        self._geoms_m: List[Any] = []
        self._props: List[Dict[str, Any]] = []
        self._tree: Optional[STRtree] = None
        self._ll_to_m = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

    def load(self) -> None:
        if self._loaded:
            return
        data = json.loads(self.ruas_path.read_text(encoding="utf-8"))
        feats = data.get("features", [])
        for f in feats:
            geom = f.get("geometry")
            if not geom:
                continue
            g = shape(geom)
            if g.is_empty:
                continue
            props = f.get("properties") or {}
            gm = transform(lambda x, y, z=None: self._ll_to_m.transform(x, y), g)
            self._geoms_m.append(gm)
            self._props.append(props)
        self._tree = STRtree(self._geoms_m)
        self._loaded = True

    def nearest_street(self, lon: float, lat: float, radius_m: float = 100.0) -> Optional[StreetHit]:
        self.load()
        assert self._tree is not None

        px, py = self._ll_to_m.transform(lon, lat)
        p = Point(px, py)
        g_near = self._tree.nearest(p)
        if g_near is None:
            return None

        dist = p.distance(g_near)
        if dist > radius_m:
            return None

        # localizar índice
        try:
            idx = self._geoms_m.index(g_near)
        except ValueError:
            # fallback
            idx = 0
        props = self._props[idx]
        return StreetHit(
            name=_infer_name(props),
            street_type=_infer_type(props),
            distance_m=float(dist),
        )


_INDEX: Optional[StreetsIndex] = None


def get_streets_index() -> StreetsIndex:
    global _INDEX
    if _INDEX is None:
        _INDEX = StreetsIndex()
    return _INDEX


def find_street(lon: float, lat: float, radius_m: float = 100.0) -> Optional[Dict[str, Any]]:
    hit = get_streets_index().nearest_street(lon, lat, radius_m)
    if not hit:
        return None
    return {"name": hit.name, "street_type": hit.street_type, "distance_m": hit.distance_m}
