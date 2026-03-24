from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import streamlit.components.v1 as components

_FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"
_component_func = components.declare_component(
    "google_map_component",
    path=str(_FRONTEND_DIR),
)


def render_google_map(
    *,
    api_key: str,
    center_lat: float,
    center_lng: float,
    zoom: int = 12,
    click_lat: Optional[float] = None,
    click_lng: Optional[float] = None,
    radius_m: int = 100,
    zones_geojson: Optional[Dict[str, Any]] = None,
    show_radius: bool = True,
    show_zones: bool = True,
    height: int = 420,
    key: Optional[str] = None,
) -> Dict[str, Any] | None:
    payload = {
        "apiKey": api_key,
        "centerLat": center_lat,
        "centerLng": center_lng,
        "zoom": int(zoom),
        "clickLat": click_lat,
        "clickLng": click_lng,
        "radiusM": int(radius_m),
        "zonesGeoJson": zones_geojson,
        "showRadius": bool(show_radius),
        "showZones": bool(show_zones),
        "height": int(height),
    }
    return _component_func(data=payload, default=None, key=key)
