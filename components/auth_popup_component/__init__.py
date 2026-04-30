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
    restore_token: bool = True,
    clear_browser_token: bool = False,
) -> Optional[str]:
    return _auth_popup_component(
        auth_url=auth_url,
        label=label,
        subtle=bool(subtle),
        restore_token=bool(restore_token),
        clear_browser_token=bool(clear_browser_token),
        default=None,
        key=key,
    )
