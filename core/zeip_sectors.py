from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List

import streamlit as st
from shapely.geometry import shape, Point
from shapely.prepared import prep
from shapely.strtree import STRtree

DATA_DIR = Path("data")
ZEIP_FILE = DATA_DIR / "zeip_setores.geojson"


@st.cache_data(show_spinner=False)
def _load_geojson(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@st.cache_resource(show_spinner=False)
def _build_zeip_index() -> Tuple[List[Any], STRtree, Dict[int, Dict[str, Any]]]:
    """
    Carrega os setores ZEIP (GeoJSON) e monta um STRtree.
    Retorna (geoms, tree, props_by_id).
    props_by_id usa id(geom) -> properties.
    """
    if not ZEIP_FILE.exists():
        return [], STRtree([]), {}

    gj = _load_geojson(ZEIP_FILE)
    feats = gj.get("features", []) or []

    geoms: List[Any] = []
    props_by_id: Dict[int, Dict[str, Any]] = {}

    for f in feats:
        try:
            g = shape(f["geometry"])
            p = f.get("properties", {}) or {}
            geoms.append(g)
            props_by_id[id(g)] = p
        except Exception:
            continue

    tree = STRtree(geoms) if geoms else STRtree([])
    return geoms, tree, props_by_id


def zeip_sector_from_latlon(lat: float, lon: float) -> Optional[str]:
    """
    Retorna o subzone_code do setor ZEIP onde o ponto cai (ex.: 'ZEIP_1'..'ZEIP_9').
    Se não encontrar, retorna None.
    """
    geoms, tree, props_by_id = _build_zeip_index()
    if not geoms:
        return None

    pt = Point(lon, lat)
    candidates = tree.query(pt)

    for g in candidates:
        try:
            if prep(g).contains(pt):
                p = props_by_id.get(id(g), {}) or {}
                code = p.get("subzone_code")
                if code:
                    return str(code)

                # fallback: tenta ler pelo nome
                name = str(p.get("name", ""))
                import re
                m = re.search(r"ZEIP\s*([1-9])", name, re.IGNORECASE)
                if m:
                    return f"ZEIP_{m.group(1)}"
        except Exception:
            continue
    return None
