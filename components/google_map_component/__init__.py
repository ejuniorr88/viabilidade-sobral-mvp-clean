from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import streamlit.components.v1 as components

_FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"

_google_map_component = components.declare_component(
    "google_map_component",
    path=str(_FRONTEND_DIR),
)


def render_google_map(
    *,
    api_key: str,
    center_lat: float,
    center_lng: float,
    zoom: int = 12,
    click_lat: float | None = None,
    click_lng: float | None = None,
    radius_m: int = 100,
    zones_geojson: Dict[str, Any] | None = None,
    height: int = 420,
) -> Optional[Dict[str, Any]]:
    return _google_map_component(
        api_key=api_key,
        center_lat=float(center_lat),
        center_lng=float(center_lng),
        zoom=int(zoom),
        click_lat=None if click_lat is None else float(click_lat),
        click_lng=None if click_lng is None else float(click_lng),
        radius_m=int(radius_m),
        zones_geojson=zones_geojson,
        height=int(height),
        default=None,
    )
