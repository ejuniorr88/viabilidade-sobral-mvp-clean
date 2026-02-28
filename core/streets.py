from __future__ import annotations

"""Streets (ruas) — rebuilt, simple, robust.

BLOCO 3 — INTEGRAÇÃO (DEV) + DIAGNÓSTICO
Objetivo:
- Garantir que o app sempre funcione, mesmo se não achar via.
- Confirmar se data/ruas.json está sendo carregado no deploy.
- Distância sempre em METROS (UTM 24S / EPSG:31984).

Regras:
- Se via não encontrada -> retorna None
- Sem fallback hardcoded
- Sem inventar propriedades
- Fail-safe: nenhuma exceção deve quebrar o app

API usada pelo app:
- find_street(lat, lon, radius_m=150.0) -> dict | None
- streets_health() -> dict (diagnóstico)
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform as shp_transform
from shapely.strtree import STRtree


# -----------------------------
# Paths (robusto no Streamlit)
# -----------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
RUAS_FILE = DATA_DIR / "ruas.json"


# -----------------------------
# CRS / Transformer
# -----------------------------
# WGS84 lon/lat (EPSG:4326) -> SIRGAS 2000 / UTM 24S (EPSG:31984) => metros
_WGS84_TO_UTM24S = Transformer.from_crs("EPSG:4326", "EPSG:31984", always_xy=True).transform


@dataclass(frozen=True)
class StreetHit:
    name: str
    street_type: Optional[str]
    distance_m: float


class StreetsIndex:
    """Índice de ruas com STRtree (geometrias WGS84).

    Estratégia:
    - Indexa em WGS84 (rápido).
    - Para medir distância, converte para UTM 24S (metros).
    - Para buscar a rua mais próxima, usa tree.nearest(point),
      então mede a distância e valida pelo radius_m.
    """

    def __init__(self, ruas_file: Path = RUAS_FILE) -> None:
        self.ruas_file = ruas_file
        self._tree: Optional[STRtree] = None
        self._geoms: List[Any] = []
        self._meta_by_geom_id: Dict[int, Dict[str, Any]] = {}
        self._built: bool = False

    def build(self) -> "StreetsIndex":
        try:
            features = self._load_features(self.ruas_file)
            self._ingest(features)
            self._tree = STRtree(self._geoms) if self._geoms else None
        except Exception:
            self._tree = None
            self._geoms = []
            self._meta_by_geom_id = {}
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

    def _ingest(self, features: List[Dict[str, Any]]) -> None:
        geoms: List[Any] = []
        meta: Dict[int, Dict[str, Any]] = {}

        for feat in features:
            try:
                geom_obj = feat.get("geometry") if isinstance(feat, dict) else None
                if not geom_obj:
                    continue
                geom = shape(geom_obj)
                if geom.is_empty:
                    continue

                props = feat.get("properties") if isinstance(feat, dict) else None
                props = props if isinstance(props, dict) else {}

                name = (
                    props.get("name")
                    or props.get("nome")
                    or props.get("rua")
                    or props.get("logradouro")
                    or ""
                )
                street_type = props.get("type") or props.get("tipo") or None

                geoms.append(geom)
                meta[id(geom)] = {
                    "name": str(name).strip(),
                    "type": (str(street_type).strip() if street_type is not None else None),
                }
            except Exception:
                continue

        self._geoms = geoms
        self._meta_by_geom_id = meta

    def nearest(self, lat: float, lon: float, radius_m: float = 150.0) -> Optional[StreetHit]:
        try:
            if not self._built:
                self.build()

            if not self._tree or not self._geoms:
                return None

            radius_m = float(radius_m)
            if radius_m <= 0:
                return None

            pt_wgs = Point(float(lon), float(lat))

            # Pega a geometria mais próxima (independente do raio)
            try:
                nearest_geom = self._tree.nearest(pt_wgs)
            except Exception:
                # Se por algum motivo nearest falhar, não quebra o app
                return None

            if nearest_geom is None:
                return None

            # Mede distância em METROS
            pt_utm = shp_transform(_WGS84_TO_UTM24S, pt_wgs)
            g_utm = shp_transform(_WGS84_TO_UTM24S, nearest_geom)
            d = float(pt_utm.distance(g_utm))

            if d > radius_m:
                return None

            m = self._meta_by_geom_id.get(id(nearest_geom), {})
            return StreetHit(
                name=m.get("name", ""),
                street_type=m.get("type", None),
                distance_m=d,
            )
        except Exception:
            return None


_INDEX_SINGLETON: Optional[StreetsIndex] = None


def get_streets_index() -> StreetsIndex:
    global _INDEX_SINGLETON
    if _INDEX_SINGLETON is None:
        _INDEX_SINGLETON = StreetsIndex().build()
    return _INDEX_SINGLETON


def find_street(lat: float, lon: float, radius_m: float = 150.0) -> Optional[Dict[str, Any]]:
    try:
        hit = get_streets_index().nearest(lat=lat, lon=lon, radius_m=radius_m)
        if hit is None:
            return None
        return {"name": hit.name, "type": hit.street_type, "distance_m": hit.distance_m}
    except Exception:
        return None


def streets_health() -> Dict[str, Any]:
    """Diagnóstico simples (não quebra o app)."""
    try:
        idx = get_streets_index()
        file_exists = RUAS_FILE.exists()
        count = len(getattr(idx, "_geoms", []))
        bbox = None
        if count:
            try:
                minx = min(g.bounds[0] for g in idx._geoms)  # type: ignore[attr-defined]
                miny = min(g.bounds[1] for g in idx._geoms)  # type: ignore[attr-defined]
                maxx = max(g.bounds[2] for g in idx._geoms)  # type: ignore[attr-defined]
                maxy = max(g.bounds[3] for g in idx._geoms)  # type: ignore[attr-defined]
                bbox = {"min_lon": float(minx), "min_lat": float(miny), "max_lon": float(maxx), "max_lat": float(maxy)}
            except Exception:
                bbox = None

        return {
            "ruas_file": str(RUAS_FILE),
            "ruas_file_exists": bool(file_exists),
            "streets_loaded": int(count),
            "bbox_wgs84": bbox,
        }
    except Exception:
        return {"ruas_file": str(RUAS_FILE), "ruas_file_exists": False, "streets_loaded": 0, "bbox_wgs84": None}
