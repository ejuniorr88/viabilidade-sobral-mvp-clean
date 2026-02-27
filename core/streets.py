from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from shapely.geometry import Point, shape
from shapely.ops import transform
from shapely.strtree import STRtree
from pyproj import Transformer

# =============================
# Files
# =============================
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


def _looks_lonlat(x: float, y: float) -> bool:
    return (-180.0 <= x <= 180.0) and (-90.0 <= y <= 90.0)


class StreetsIndex:
    """Índice espacial das vias (ruas.json).

    Assume ruas.json em EPSG:4326 (lon/lat) e projeta para EPSG:3857 (metros)
    para cálculo de distâncias.

    Importante: always_xy=True evita inversão de eixo (lat/lon), que é a causa
    mais comum de 'Via não encontrada' mesmo com o pin em cima da rua.
    """

    def __init__(self) -> None:
        self._tree: Optional[STRtree] = None
        self._geoms_3857: List[Any] = []
        self._props: List[Dict[str, Any]] = []

        self._to_3857 = Transformer.from_crs(
            "EPSG:4326", "EPSG:3857", always_xy=True
        ).transform

    def load(self) -> None:
        if self._tree is not None:
            return

        if not RUAS_FILE.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {RUAS_FILE}")

        with RUAS_FILE.open("r", encoding="utf-8") as f:
            gj = json.load(f)

        feats = gj.get("features") if isinstance(gj, dict) else None
        if not feats:
            raise RuntimeError("ruas.json inválido: esperado FeatureCollection com 'features'.")

        geoms_3857: List[Any] = []
        props_list: List[Dict[str, Any]] = []

        for feat in feats:
            geom = feat.get("geometry")
            props = feat.get("properties") or {}
            if not geom:
                continue

            g = shape(geom)  # em 4326
            g3857 = transform(self._to_3857, g)  # em metros

            geoms_3857.append(g3857)
            props_list.append(props)

        if not geoms_3857:
            raise RuntimeError("ruas.json não contém geometrias válidas.")

        self._geoms_3857 = geoms_3857
        self._props = props_list
        self._tree = STRtree(self._geoms_3857)

    def nearest_street(self, lon: float, lat: float, radius_m: float) -> Optional[StreetHit]:
        self.load()
        assert self._tree is not None

        # Se o app mandar invertido, tenta corrigir
        if _looks_lonlat(lat, lon) and not _looks_lonlat(lon, lat):
            lon, lat = lat, lon

        p = Point(float(lon), float(lat))
        p3857 = transform(self._to_3857, p)

        buf = p3857.buffer(float(radius_m))
        candidates = self._tree.query(buf)
        if not candidates:
            return None

        best_idx: Optional[int] = None
        best_d: Optional[float] = None

        # STRtree retorna geometrias; achamos índice pelo objeto
        for g in candidates:
            try:
                i = self._geoms_3857.index(g)
            except ValueError:
                continue
            d = float(p3857.distance(g))
            if best_d is None or d < best_d:
                best_d = d
                best_idx = i

        if best_idx is None or best_d is None or best_d > float(radius_m):
            return None

        props = self._props[best_idx]
        return StreetHit(
            name=_infer_name(props),
            street_type=_infer_type(props),
            distance_m=best_d,
        )


_INDEX: Optional[StreetsIndex] = None


def get_streets_index() -> StreetsIndex:
    global _INDEX
    if _INDEX is None:
        _INDEX = StreetsIndex()
    return _INDEX


def find_street(lon: float, lat: float, radius_m: float) -> Optional[StreetHit]:
    idx = get_streets_index()
    return idx.nearest_street(lon=lon, lat=lat, radius_m=radius_m)
