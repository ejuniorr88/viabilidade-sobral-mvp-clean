from __future__ import annotations

import os
import json
from typing import Any, Dict

import streamlit as st

from core.env_secrets import get_secret, get_secret_str


def _build_public_storage_url(bucket: str, path: str) -> str | None:
    base = os.getenv("SUPABASE_URL", "").rstrip("/")
    if not base:
        try:
            base = (get_secret("SUPABASE_URL") or "").rstrip("/")
        except Exception:
            base = ""
    if not base or not bucket or not path:
        return None
    path = path.lstrip("/")
    return f"{base}/storage/v1/object/public/{bucket}/{path}"


def _extract_figures_from_rule(rule: Dict[str, Any]) -> list[Dict[str, Any]]:
    if not isinstance(rule, dict):
        return []
    src = rule.get("src") or {}
    if isinstance(src, str):
        try:
            src = json.loads(src)
        except Exception:
            src = {}
    if not isinstance(src, dict):
        return []
    figs = src.get("figures") or src.get("figuras") or []
    if not isinstance(figs, list):
        return []
    out: list[Dict[str, Any]] = []
    for it in figs:
        if isinstance(it, dict) and it.get("bucket") and it.get("path"):
            out.append(it)
    return out


def _extract_figure_number(figure: Dict[str, Any]) -> int | None:
    title = str(figure.get("title") or figure.get("titulo") or "")
    path = str(figure.get("path") or "")
    text = f"{title} {path}".lower()
    for n in range(1, 8):
        candidates = [
            f"figura {n}", f"figura_{n}", f"figura-{n}",
            f"fig {n}", f"fig_{n}", f"fig-{n}",
            f"anexo v {n}", f"/{n}.", f"_{n}.", f"-{n}.",
        ]
        if any(c in text for c in candidates):
            return n
    return None


def filter_figuras_by_lot_type(figs: list[Dict[str, Any]], is_corner: bool = False) -> list[Dict[str, Any]]:
    allowed = {5, 6, 7} if is_corner else {1, 2, 3, 4}
    filtered = [f for f in figs if _extract_figure_number(f) in allowed]
    return filtered or figs


def render_figuras_anexo_v(rule: Dict[str, Any], is_corner: bool = False) -> None:
    figs = filter_figuras_by_lot_type(_extract_figures_from_rule(rule), is_corner=is_corner)
    if figs:
        st.markdown("---\n### 📎 Figuras anexas (Anexo V)")
        for i in range(0, len(figs), 2):
            cols = st.columns(2)
            pair = figs[i : i + 2]
            for col, f in zip(cols, pair):
                with col:
                    title = f.get("title") or f.get("titulo")
                    caption = f.get("caption") or f.get("legenda")
                    bucket = f.get("bucket")
                    path = f.get("path")
                    url = _build_public_storage_url(str(bucket), str(path)) if bucket and path else None
                    if title:
                        st.markdown(f"**{title}**")
                    if url:
                        st.image(url, caption=caption or title or "", use_container_width=True)
                        st.markdown(f"[🔎 Abrir em tamanho real]({url})")
                    else:
                        st.markdown(f"Imagem: {bucket}/{path}")
                    if caption and caption != title:
                        st.caption(caption)
