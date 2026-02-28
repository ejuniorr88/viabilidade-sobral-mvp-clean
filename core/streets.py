from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from shapely.geometry import Point, shape
from shapely.ops import transform
from shapely.strtree import STRtree
from pyproj import Transformer


DATA_DIR = Path("data")
RUAS_FILE = DATA_DIR / "ruas.json"

# EPSG:31984 = SIRGAS 2000 / UTM zone 24S (m)
_TRANSFORMER_LL_TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:31984", always_xy=True)


@dataclass(frozen=True)
class StreetHit:
    name: str
    street_type: Optional[str]
    distance_m: float
    reason: Optional[str] = None


def _infer_name(props: Dict[str, Any]) -> str:
    for k in ("log_ofic", "nome", "name", "logradouro", "rua", "via"):
        v = props.get(k)
        if v:
            return str(v).strip()
    return "Via (sem nome)"


def _infer_type(props: Dict[str, Any]) -> Optional[str]:
    for k in ("hierarquia", "tipo", "type", "categoria", "class", "highway"):
        v = props.get(k)
        if v:
            return str(v).strip()
    return None


def _looks_lonlat(g) -> bool:
    """
    Heurística simples:
    - lon/lat geralmente estão em faixas [-180..180] e [-90..90]
    - se estiver muito fora disso, provavelmente já está projetado
    """
    try:
        minx, miny, maxx, maxy = g.bounds
        return (-180 <= minx <= 180) and (-180 <= maxx <= 180) and (-90 <= miny <= 90) and (-90 <= maxy <= 90)
    except Exception:
        return True


class StreetsIndex:
    def __init__(self) -> None:
        self.ok: bool = False
        self.reason: str = ""
        self._tree: Optional[STRtree] = None
        self._geoms: list = []
        self._props: list[Dict[str, Any]] = []

    def load(self, ruas_file: Path = RUAS_FILE) -> "StreetsIndex":
        if not ruas_file.exists():
            self.ok = False
            self.reason = f"Arquivo não encontrado: {ruas_file}"
            return self

        try:
            gj = json.loads(ruas_file.read_text(encoding="utf-8"))
        except Exception as e:
            self.ok = False
            self.reason = f"Falha ao ler JSON de ruas: {e}"
            return self

        feats = gj.get("features", [])
        if not feats:
            self.ok = False
            self.reason = "GeoJSON de ruas sem features."
            return self

        ll_to_utm = _TRANSFORMER_LL_TO_UTM.transform

        geoms_utm = []
        props_list = []

        # 1) tentar interpretar como lon/lat e transformar pra UTM
        for feat in feats:
            geom = feat.get("geometry")
            if not geom:
                continue
            try:
                g = shape(geom)
                if _looks_lonlat(g):
                    g_utm = transform(ll_to_utm, g)
                else:
                    # já projetado? assume que já está em metros
                    g_utm = g
                geoms_utm.append(g_utm)
                props_list.append(feat.get("properties", {}) or {})
            except Exception:
                continue

        if not geoms_utm:
            self.ok = False
            self.reason = "Nenhuma geometria de rua válida no GeoJSON."
            return self

        try:
            self._tree = STRtree(geoms_utm)
        except Exception as e:
            self.ok = False
            self.reason = f"Falha ao criar índice espacial (STRtree): {e}"
            return self

        self._geoms = geoms_utm
        self._props = props_list
        self.ok = True
        self.reason = ""
        return self

    def nearest_street(self, lon: float, lat: float, radius_m: float) -> StreetHit:
        if not self.ok or self._tree is None:
            return StreetHit(
                name="Via não encontrada",
                street_type=None,
                distance_m=math.inf,
                reason=self.reason or "Índice de ruas não carregado.",
            )

        ll_to_utm = _TRANSFORMER_LL_TO_UTM.transform

        try:
            x, y = ll_to_utm(lon, lat)
        except Exception as e:
            return StreetHit(
                name="Via não encontrada",
                street_type=None,
                distance_m=math.inf,
                reason=f"Falha ao converter clique para UTM: {e}",
            )

        p = Point(x, y)

        try:
            g_near = self._tree.nearest(p)
            if g_near is None:
                return StreetHit("Via não encontrada", None, math.inf, "STRtree.nearest retornou None.")
            dist = float(p.distance(g_near))
        except Exception as e:
            return StreetHit("Via não encontrada", None, math.inf, f"Erro ao buscar via mais próxima: {e}")

        if dist > float(radius_m):
            return StreetHit(
                name="Via não encontrada",
                street_type=None,
                distance_m=dist,
                reason=f"Mais próxima a {dist:.1f} m (raio {radius_m:.0f} m).",
            )

        # pegar properties da geometria
        idx = None
        try:
            idx = self._geoms.index(g_near)
        except Exception:
            # fallback por igualdade geométrica
            for j, g in enumerate(self._geoms):
                try:
                    if g.equals(g_near):
                        idx = j
                        break
                except Exception:
                    continue
        if idx is None:
            idx = 0

        props = self._props[idx] if idx < len(self._props) else {}
        name = _infer_name(props)
        stype = _infer_type(props)

        return StreetHit(name=name, street_type=stype, distance_m=dist, reason=None)


# singleton simples (evita recarregar a cada chamada)
_INDEX: Optional[StreetsIndex] = None


def get_streets_index() -> StreetsIndex:
    global _INDEX
    if _INDEX is None:
        _INDEX = StreetsIndex().load(RUAS_FILE)
    return _INDEX


def find_street(lon: float, lat: float, radius_m: float) -> StreetHit:
    return get_streets_index().nearest_street(lon, lat, radius_m)
