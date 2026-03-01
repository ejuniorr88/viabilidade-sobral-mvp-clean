from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from numbers import Integral, Union

from shapely.geometry import Point, shape
from shapely.ops import transform as shp_transform
from shapely.strtree import STRtree
from pyproj import Transformer

DATA_DIR = Path("data")
RUAS_FILE = DATA_DIR / "ruas.json"

# Usamos UTM 24S (SIRGAS 2000) para distância em metros.
# (Sobral/CE cai aqui.)
_WGS84_TO_UTM24S = Transformer.from_crs("EPSG:4326", "EPSG:31984", always_xy=True)


@dataclass(frozen=True)
class StreetHit:
    name: str
    street_type: Optional[str]
    distance_m: float


def _infer_name(props: Dict[str, Any]) -> str:
    # prioridade: log_ofic primeiro (seu arquivo tem muito isso)
    for k in ("log_ofic", "nome", "name", "logradouro", "rua", "via"):
        v = props.get(k)
        if v:
            s = str(v).strip()
            if s:
                return s
    return "Via (sem nome)"


def _infer_type(props: Dict[str, Any]) -> Optional[str]:
    for k in ("hierarquia", "tipo", "type", "categoria", "class", "highway"):
        v = props.get(k)
        if v:
            s = str(v).strip()
            if s:
                return s
    return None


class StreetsIndex:
    """
    Índice espacial robusto:
    - Funciona com Shapely 1.x (STRtree.query -> geometrias)
    - Funciona com Shapely 2.x (STRtree.query -> índices / numpy array)
    """

    def __init__(self) -> None:
        self._tree: Optional[STRtree] = None
        self._geoms_utm: List[Any] = []
        self._props: List[Dict[str, Any]] = []
        self._id_to_idx: Dict[int, int] = {}
        self._loaded: bool = False

    def load(self) -> None:
        if self._loaded:
            return
        self._loaded = True

        if not RUAS_FILE.exists():
            self._tree = STRtree([])
            self._geoms_utm = []
            self._props = []
            self._id_to_idx = {}
            return

        data = json.loads(RUAS_FILE.read_text(encoding="utf-8"))
        feats = data.get("features", []) or []

        geoms: List[Any] = []
        props_list: List[Dict[str, Any]] = []

        ll_to_utm = _WGS84_TO_UTM24S.transform

        for f in feats:
            g = f.get("geometry")
            if not g:
                continue
            try:
                geom_ll = shape(g)
            except Exception:
                continue

            try:
                geom_utm = shp_transform(ll_to_utm, geom_ll)
            except Exception:
                continue

            props = f.get("properties", {}) or {}
            geoms.append(geom_utm)
            props_list.append(props)

        self._geoms_utm = geoms
        self._props = props_list
        self._id_to_idx = {id(g): i for i, g in enumerate(self._geoms_utm)}
        self._tree = STRtree(self._geoms_utm)

    def nearest_street(self, lat: float, lon: float, radius_m: float = 200.0) -> Optional[StreetHit]:
        self.load()
        if not self._tree or not self._geoms_utm:
            return None

        # ponto em UTM (m)
        x, y = _WGS84_TO_UTM24S.transform(float(lon), float(lat))
        p = Point(x, y)

        # candidatos no buffer (m)
        buf = p.buffer(float(radius_m))
        cand = self._tree.query(buf)

        if cand is None:
            return None

        # Shapely 2 pode devolver array de índices; Shapely 1 devolve geometrias
        cand_list: List[Union[int, Any]]
        try:
            cand_list = list(cand)
        except Exception:
            cand_list = []

        if not cand_list:
            return None

        best_idx: Optional[int] = None
        best_dist = float("inf")

        first = cand_list[0]
        if isinstance(first, Integral):
            # shapely 2 (índices)
            for idx in cand_list:
                if not isinstance(idx, Integral):
                    continue
                if idx < 0 or idx >= len(self._geoms_utm):
                    continue
                g = self._geoms_utm[idx]
                d = float(p.distance(g))
                if d < best_dist:
                    best_dist = d
                    best_idx = idx
        else:
            # shapely 1 (geometrias)
            for g in cand_list:
                idx = self._id_to_idx.get(id(g))
                if idx is None:
                    continue
                d = float(p.distance(g))
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


def find_street(lat: float, lon: float, radius_m: float = 200.0) -> Optional[Dict[str, Any]]:
    hit = get_streets_index().nearest_street(lat=lat, lon=lon, radius_m=radius_m)
    if not hit:
        return None
    return {"name": hit.name, "type": hit.street_type, "distance_m": hit.distance_m}
