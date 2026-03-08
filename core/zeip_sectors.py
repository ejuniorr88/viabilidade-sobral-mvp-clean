from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List

import streamlit as st
from shapely.geometry import shape, Point
from shapely.prepared import prep
from shapely.strtree import STRtree

DATA_DIR = Path("data")
ZEIS_FILE = DATA_DIR / "zeis_setores.geojson"  # coloque aqui o arquivo exportado do QGIS


@st.cache_data(show_spinner=False)
def _load_geojson(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@st.cache_resource(show_spinner=False)
def _build_zeis_index() -> Tuple[List[Any], STRtree, Dict[int, Dict[str, Any]]]:
    """Índice espacial para ZEIS 1/2/3 (igual a ZEIP)."""
    if not ZEIS_FILE.exists():
        return [], STRtree([]), {}

    gj = _load_geojson(ZEIS_FILE)
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


def zeis_sector_from_latlon(lat: float, lon: float) -> Optional[str]:
    """
    Retorna 'ZEIS 1' / 'ZEIS 2' / 'ZEIS 3' conforme o polígono onde o ponto cai.
    """
    geoms, tree, props_by_id = _build_zeis_index()
    if not geoms:
        return None

    pt = Point(lon, lat)

    try:
        candidates = tree.query(pt)
    except Exception:
        candidates = geoms

    for g in candidates:
        try:
            if g.covers(pt) or g.buffer(1e-12).covers(pt):
                p = props_by_id.get(id(g), {}) or {}
                sub = p.get("subzona") or p.get("SUBZONA") or p.get("zona_sigla") or p.get("ZONA_SIGLA")
                if sub:
                    sub = str(sub).strip()
                    # normaliza "ZEIS2" -> "ZEIS 2"
                    import re
                    m = re.search(r"ZEIS\D*([123])", sub.upper())
                    if m:
                        return f"ZEIS {m.group(1)}"
                # fallback pelo texto do name/description
                name = str(p.get("name", p.get("NAME", "")))
                import re
                m = re.search(r"ZEIS\D*([123])", name.upper())
                if m:
                    return f"ZEIS {m.group(1)}"
        except Exception:
            continue

    # fallback: setor mais próximo (evita buracos/bordas)
    try:
        nearest = min(geoms, key=lambda gg: gg.distance(pt))
        d = float(nearest.distance(pt))
        if d <= 0.0002:
            p = props_by_id.get(id(nearest), {}) or {}
            sub = p.get("subzona") or p.get("SUBZONA")
            if sub:
                import re
                m = re.search(r"ZEIS\D*([123])", str(sub).upper())
                if m:
                    return f"ZEIS {m.group(1)}"
    except Exception:
        pass

    return None
