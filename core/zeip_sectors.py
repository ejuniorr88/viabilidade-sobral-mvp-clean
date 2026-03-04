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
def _build_zeip_index() -> Tuple[List[Any], STRtree, List[Dict[str, Any]], Dict[int, int]]:
    """
    Carrega os setores ZEIP (GeoJSON) e monta um STRtree.
    Retorna (geoms, tree, props, id_map) onde id_map mapeia id(geom)->index.
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
    id_map = {id(g): i for i, g in enumerate(geoms)}
    return geoms, tree, props, id_map


def zeip_sector_from_latlon(lat: float, lon: float) -> Optional[str]:
    """
    Retorna o subzone_code do setor ZEIP onde o ponto cai (ex.: 'ZEIP_1'..'ZEIP_9').
    Se não encontrar, retorna None.

    Observação: usa covers() (inclui bordas) para evitar falhas quando o clique cai na linha do polígono.
    """
    geoms, tree, props, id_map = _build_zeip_index()
    if not geoms:
        return None

    pt = Point(lon, lat)
    candidates = tree.query(pt)

    for g in candidates:
        try:
            # covers inclui bordas; prepared geometry não tem covers, então usa o próprio geom
            if g.covers(pt) or g.buffer(1e-12).covers(pt):
                idx = id_map.get(id(g))
                if idx is None:
                    continue
                p = props[idx] or {}
                code = p.get("subzone_code")
                if code:
                    return str(code)

                # fallback: tentar pelo nome "ZEIP 1"
                name = str(p.get("name", ""))
                import re
                m = re.search(r"ZEIP\s*([1-9])", name, re.IGNORECASE)
                if m:
                    return f"ZEIP_{m.group(1)}"
        except Exception:
            continue

    return None
