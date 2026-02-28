from __future__ import annotations

"""Streets (ruas) — rebuilt, simple, robust, isolated.

BLOCO 2 — RECONSTRUÇÃO DO STREETS DO ZERO
Escopo:
- Leitura de data/ruas.json
- CRS correto e distância em metros via UTM 24S (SIRGAS 2000) EPSG:31984
- Índice espacial com STRtree
- nearest (via mais próxima dentro de radius_m)
Regras:
- Se via não for encontrada -> retorna None (app continua)
- Sem fallback hardcoded
- Sem inventar propriedades
- Nenhuma exceção deve quebrar o app

Interface preservada para integração:
- find_street(lat, lon, radius_m=150.0) -> dict | None
- get_streets_index() -> StreetsIndex (singleton lazy)
"""

import json
from dataclasses import dataclass
from math import cos, radians
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pyproj import Transformer
from shapely.geometry import Point, box, shape
from shapely.ops import transform as shp_transform
from shapely.strtree import STRtree


# -----------------------------
# Paths
# -----------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
RUAS_FILE = DATA_DIR / "ruas.json"


# -----------------------------
# CRS / Transformer
# -----------------------------
# WGS84 lon/lat (EPSG:4326) -> SIRGAS 2000 / UTM 24S (EPSG:31984), metros
_WGS84_TO_UTM24S = Transformer.from_crs("EPSG:4326", "EPSG:31984", always_xy=True).transform


# -----------------------------
# Types
# -----------------------------
@dataclass(frozen=True)
class StreetHit:
    name: str
    street_type: Optional[str]
    distance_m: float


class StreetsIndex:
    """Índice de ruas (STRtree) com cálculo de distância em metros.

    Design:
    - Armazena geometrias em WGS84 (para indexação)
    - Converte para UTM apenas durante cálculo de distância (metros)
    - Carregamento e consultas são fail-safe (nunca levantam exceção para fora)
    """

    def __init__(self, ruas_file: Path = RUAS_FILE) -> None:
        self.ruas_file = ruas_file
        self._tree: Optional[STRtree] = None
        self._geoms: List[Any] = []
        self._meta_by_geom_id: Dict[int, Dict[str, Any]] = {}
        self._built: bool = False

    # ---------- Build ----------
    def build(self) -> "StreetsIndex":
        """Carrega ruas.json e constrói a STRtree.

        Fail-safe:
        - Se arquivo não existir, JSON inválido, geometria inválida, etc -> índice vazio.
        """
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
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)

        # Aceita FeatureCollection ou lista de features
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

                # Sem inventar: tenta chaves comuns, senão string vazia
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

    # ---------- Query ----------
    def nearest(self, lat: float, lon: float, radius_m: float = 150.0) -> Optional[StreetHit]:
        """Retorna a via mais próxima dentro de radius_m (metros) ou None.

        Fail-safe total: nunca levanta exceção para fora.
        """
        try:
            if not self._built:
                self.build()

            if not self._tree or not self._geoms:
                return None

            radius_m = float(radius_m)
            if radius_m <= 0:
                return None

            lat_f = float(lat)
            lon_f = float(lon)

            pt_wgs = Point(lon_f, lat_f)

            # Bounding-box aproximado em graus (apenas para filtrar candidatos do STRtree)
            # 1 grau latitude ~ 111_320 m; longitude ajusta por cos(lat).
            deg_lat = radius_m / 111_320.0
            deg_lon = radius_m / (111_320.0 * max(0.1, cos(radians(lat_f))))

            query_geom = box(pt_wgs.x - deg_lon, pt_wgs.y - deg_lat, pt_wgs.x + deg_lon, pt_wgs.y + deg_lat)

            candidates = list(self._tree.query(query_geom))
            if not candidates:
                return None

            # Distância em metros: converte ponto e cada candidato para UTM e mede distância
            pt_utm = shp_transform(_WGS84_TO_UTM24S, pt_wgs)

            best: Optional[Tuple[float, Any]] = None
            for g in candidates:
                try:
                    g_utm = shp_transform(_WGS84_TO_UTM24S, g)
                    d = float(pt_utm.distance(g_utm))
                    if best is None or d < best[0]:
                        best = (d, g)
                except Exception:
                    continue

            if best is None:
                return None

            best_d, best_geom = best
            if best_d > radius_m:
                return None

            m = self._meta_by_geom_id.get(id(best_geom), {})
            return StreetHit(
                name=m.get("name", ""),
                street_type=m.get("type", None),
                distance_m=best_d,
            )
        except Exception:
            return None

def streets_health() -> Dict[str, Any]:
    """Retorna informações simples para diagnóstico (sem quebrar o app)."""
    try:
        idx = get_streets_index()
        file_exists = RUAS_FILE.exists()
        count = len(getattr(idx, "_geoms", []))
        # bbox aproximado das geometrias (WGS84) se existir
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
        return {
            "ruas_file": str(RUAS_FILE),
            "ruas_file_exists": bool(RUAS_FILE.exists()),
            "streets_loaded": 0,
            "bbox_wgs84": None,
        }


# -----------------------------
# Singleton + public API
# -----------------------------
_INDEX_SINGLETON: Optional[StreetsIndex] = None


def get_streets_index() -> StreetsIndex:
    """Obtém singleton do índice de ruas (lazy)."""
    global _INDEX_SINGLETON
    if _INDEX_SINGLETON is None:
        _INDEX_SINGLETON = StreetsIndex().build()
    return _INDEX_SINGLETON


def find_street(lat: float, lon: float, radius_m: float = 150.0) -> Optional[Dict[str, Any]]:
    """API usada pelo app: retorna dict simples ou None.

    Nunca levanta exceção para fora.
    """
    try:
        hit = get_streets_index().nearest(lat=lat, lon=lon, radius_m=radius_m)
        if hit is None:
            return None
        return {
            "name": hit.name,
            "type": hit.street_type,
            "distance_m": hit.distance_m,
        }
    except Exception:
        return None
