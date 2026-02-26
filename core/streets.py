from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List

from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from shapely.ops import transform
from pyproj import Transformer


@dataclass(frozen=True)
class StreetHit:
    name: str
    hierarchy: str
    distance_m: float


class StreetsIndex:
    """
    Índice espacial (STRtree) das geometrias de ruas em UTM (metros),
    para buscar a rua mais próxima do ponto clicado.
    """

    def __init__(self, geoms_utm: List[Any], props_by_id: Dict[int, Dict[str, Any]]):
        self._tree = STRtree(geoms_utm)
        self._props_by_id = props_by_id

    def nearest(self, pt_utm: Point, max_distance_m: float = 60.0) -> Optional[StreetHit]:
        if len(self._tree.geometries) == 0:
            return None

        nearest_geom = self._tree.nearest(pt_utm)
        if nearest_geom is None:
            return None

        dist = float(nearest_geom.distance(pt_utm))
        if dist > max_distance_m:
            return None

        props = self._props_by_id.get(id(nearest_geom), {}) or {}
        name = (props.get("log_ofic") or props.get("nome") or props.get("name") or "").strip()
        hierarchy = (props.get("hierarquia") or props.get("classe") or props.get("type") or "").strip()

        # fallback legível
        if not name:
            name = "Rua (sem nome no dataset)"
        if not hierarchy:
            hierarchy = "Tipo não informado"

        return StreetHit(name=name, hierarchy=hierarchy, distance_m=dist)


def load_streets_index(ruas_file: Path) -> StreetsIndex:
    """
    Espera GeoJSON em data/ruas.json.
    Converte todas as linhas para UTM 24S (SIRGAS 2000) para medir distância em metros.
    """
    data = json.loads(ruas_file.read_text(encoding="utf-8"))

    feats = []
    if isinstance(data, dict) and "features" in data:
        feats = data["features"] or []
    elif isinstance(data, list):
        feats = data
    else:
        feats = []

    # Sobral: SIRGAS 2000 / UTM 24S (EPSG:31984)
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:31984", always_xy=True)

    def _to_utm(x, y, z=None):
        return transformer.transform(x, y)

    geoms_utm: List[Any] = []
    props_by_id: Dict[int, Dict[str, Any]] = {}

    for f in feats:
        geom = (f or {}).get("geometry")
        props = (f or {}).get("properties") or {}

        if not geom:
            continue

        try:
            g = shape(geom)
        except Exception:
            continue

        # Converte para UTM (m)
        try:
            g_utm = transform(_to_utm, g)
        except Exception:
            continue

        geoms_utm.append(g_utm)
        props_by_id[id(g_utm)] = props

    return StreetsIndex(geoms_utm=geoms_utm, props_by_id=props_by_id)


def nearest_street_from_latlon(
    streets_index: StreetsIndex,
    lat: float,
    lon: float,
    max_distance_m: float = 60.0,
) -> Optional[StreetHit]:
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:31984", always_xy=True)
    x, y = transformer.transform(lon, lat)
    pt_utm = Point(x, y)
    return streets_index.nearest(pt_utm, max_distance_m=max_distance_m)
