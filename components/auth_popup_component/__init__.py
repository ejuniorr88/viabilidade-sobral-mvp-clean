from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import streamlit.components.v1 as components

_FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"

_auth_popup_component = components.declare_component(
    "auth_popup_component",
    path=str(_FRONTEND_DIR),
)


def render_auth_popup_button(
    *,
    label: str,
    auth_url: str,
    full_width: bool = False,
    subtle: bool = False,
    key: str = "vf_auth_popup_button",
) -> Optional[dict[str, Any]]:
    height = 48 if subtle else 56
    return _auth_popup_component(
        label=label,
        auth_url=auth_url,
        full_width=full_width,
        subtle=subtle,
        default=None,
        key=key,
        height=height,
    )
