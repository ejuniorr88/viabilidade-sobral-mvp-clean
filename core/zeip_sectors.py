from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
from shapely.geometry import Point, shape
from shapely.prepared import prep
from shapely.strtree import STRtree

DATA_DIR = Path("data")
ZEIP_FILE = DATA_DIR / "zeip_setores.geojson"


@st.cache_data(show_spinner=False)
def _load_geojson(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@st.cache_resource(show_spinner=False)
def _build_index() -> Tuple[List[Any], STRtree, List[Dict[str, Any]], Dict[int, int]]:
    """
    Retorna:
      geoms: lista de geometrias shapely
      tree: STRtree para query rápida
      props: lista de properties (mesmo índice de geoms)
      id_to_idx: mapa id(geom)->índice em geoms (evita .index() O(n))
    """
    if not ZEIP_FILE.exists():
        return [], STRtree([]), [], {}

    gj = _load_geojson(ZEIP_FILE)
    feats = gj.get("features", []) or []

    geoms: List[Any] = []
    props: List[Dict[str, Any]] = []
    for f in feats:
        try:
            g = shape(f["geometry"])
            geoms.append(g)
            props.append(f.get("properties", {}) or {})
        except Exception:
            continue

    tree = STRtree(geoms) if geoms else STRtree([])
    id_to_idx = {id(g): i for i, g in enumerate(geoms)}
    return geoms, tree, props, id_to_idx


def zeip_sector_from_latlon(lat: float, lon: float) -> Optional[str]:
    """
    Retorna 'ZEIP_1'..'ZEIP_9' se o ponto cair em algum setor, senão None.
    """
    geoms, tree, props, id_to_idx = _build_index()
    if not geoms:
        return None

    pt = Point(lon, lat)
    for g in tree.query(pt):
        try:
            if prep(g).contains(pt):
                p = props[id_to_idx.get(id(g), 0)] if props else {}
                code = p.get("subzone_code")
                if code:
                    return str(code)
                # fallback: tentar parsear de 'subzona' / 'name'
                import re
                name = str(p.get("subzona") or p.get("name") or "")
                m = re.search(r"ZEIP\s*([1-9])", name, re.IGNORECASE)
                if m:
                    return f"ZEIP_{m.group(1)}"
        except Exception:
            continue
    return None
