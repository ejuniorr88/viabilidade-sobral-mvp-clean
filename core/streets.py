from __future__ import annotations

"""core.streets — módulo de ruas (compatível e robusto)

Correção:
- Indexa as geometrias do ruas.json em UTM (metros) e usa STRtree.query(buffer)
  (método mais compatível) para buscar candidatos dentro do raio.
- Escolhe o menor distance() em metros.
- Se não achar -> None. Nunca quebra o app.

API:
- find_street(lat, lon, radius_m=150.0) -> dict | None
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform as shp_transform
from shapely.strtree import STRtree

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
RUAS_FILE = DATA_DIR / "ruas.json"

_WGS84_TO_UTM24S = Transformer.from_crs("EPSG:4326", "EPSG:31984", always_xy=True).transform


@dataclass(frozen=True)
class StreetHit:
    name: str
    street_type: Optional[str]
    distance_m: float


class StreetsIndex:
    def __init__(self, ruas_file: Path = RUAS_FILE) -> None:
        self.ruas_file = ruas_file
        self._tree_utm: Optional[STRtree] = None
        self._geoms_utm: List[Any] = []
        self._meta_by_id: Dict[int, Dict[str, Any]] = {}
        self._built: bool = False

    def build(self) -> "StreetsIndex":
        try:
            features = self._load_features(self.ruas_file)
            self._ingest_to_utm(features)
            self._tree_utm = STRtree(self._geoms_utm) if self._geoms_utm else None
        except Exception:
            self._tree_utm = None
            self._geoms_utm = []
            self._meta_by_id = {}
        self._built = True
        return self

    @staticmethod
    def _load_features(path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("type") == "FeatureCollection":
            feats = data.get("features") or []
            return feats if isinstance(feats, list) else []
        if isinstance(data, list):
            return data
        return []

    def _ingest_to_utm(self, features: List[Dict[str, Any]]) -> None:
        geoms_utm: List[Any] = []
        meta: Dict[int, Dict[str, Any]] = {}

        for feat in features:
            try:
                if not isinstance(feat, dict):
                    continue
                geom_obj = feat.get("geometry")
                if not geom_obj:
                    continue
                geom_wgs = shape(geom_obj)
                if geom_wgs.is_empty:
                    continue
                geom_utm = shp_transform(_WGS84_TO_UTM24S, geom_wgs)

                props = feat.get("properties")
                props = props if isinstance(props, dict) else {}

                name = (
                    props.get("name")
                    or props.get("log_ofic")
                    or props.get("logradouro")
                    or props.get("rua")
                    or props.get("nome")
                    or ""
                )
                street_type = props.get("hierarquia") or props.get("type") or props.get("tipo") or None

                geoms_utm.append(geom_utm)
                meta[id(geom_utm)] = {
                    "name": str(name).strip(),
                    "type": (str(street_type).strip() if street_type is not None else None),
                }
            except Exception:
                continue

        self._geoms_utm = geoms_utm
        self._meta_by_id = meta

    def nearest(self, lat: float, lon: float, radius_m: float) -> Optional[StreetHit]:
        try:
            if not self._built:
                self.build()
            if not self._tree_utm or not self._geoms_utm:
                return None

            radius_m = float(radius_m)
            if radius_m <= 0:
                return None

            pt_utm = shp_transform(_WGS84_TO_UTM24S, Point(float(lon), float(lat)))

            candidates = self._tree_utm.query(pt_utm.buffer(radius_m))
            if not candidates:
                return None

            best = None
            best_d = None
            for g in candidates:
                try:
                    d = float(pt_utm.distance(g))
                    if best_d is None or d < best_d:
                        best_d = d
                        best = g
                except Exception:
                    continue

            if best is None or best_d is None or best_d > radius_m:
                return None

            m = self._meta_by_id.get(id(best), {})
            return StreetHit(name=m.get("name", ""), street_type=m.get("type", None), distance_m=best_d)
        except Exception:
            return None


_INDEX: Optional[StreetsIndex] = None


def _get_index() -> StreetsIndex:
    global _INDEX
    if _INDEX is None:
        _INDEX = StreetsIndex().build()
    return _INDEX


def find_street(lat: float, lon: float, radius_m: float = 150.0) -> Optional[Dict[str, Any]]:
    try:
        hit = _get_index().nearest(lat=lat, lon=lon, radius_m=radius_m)
        if hit is None:
            return None
        return {"name": hit.name, "type": hit.street_type, "distance_m": hit.distance_m}
    except Exception:
        return None
