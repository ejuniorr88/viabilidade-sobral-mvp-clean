from __future__ import annotations

from pathlib import Path
from typing import Optional

import streamlit.components.v1 as components

_FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"

_auth_popup_component = components.declare_component(
    "auth_popup_component",
    path=str(_FRONTEND_DIR),
)


def render_auth_popup_bridge(*, key: str = "vf_auth_popup_bridge") -> Optional[dict]:
    return _auth_popup_component(default=None, key=key)
