from __future__ import annotations

from pathlib import Path
from typing import Optional

import streamlit.components.v1 as components

_FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"

_auth_popup_component = components.declare_component(
    "auth_popup_component",
    path=str(_FRONTEND_DIR),
)


def render_auth_popup_button(
    *,
    auth_url: str,
    label: str = "Entrar com Google",
    subtle: bool = False,
    key: str | None = None,
) -> Optional[str]:
    return _auth_popup_component(
        auth_url=auth_url,
        label=label,
        subtle=bool(subtle),
        default=None,
        key=key,
    )
