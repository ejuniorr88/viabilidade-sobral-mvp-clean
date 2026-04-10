
from __future__ import annotations

import os
from typing import Any

import streamlit as st


def get_secret(key: str, default: Any = None, *, required: bool = False) -> Any:
    val = os.getenv(key)
    if val not in (None, ""):
        return val
    try:
        val = st.secrets.get(key)
        if val not in (None, ""):
            return val
    except Exception:
        pass
    if required:
        raise RuntimeError(f"Secret/variável ausente: {key}")
    return default


def get_secret_str(key: str, default: str = "", *, required: bool = False) -> str:
    value = get_secret(key, default=default, required=required)
    return "" if value is None else str(value)
