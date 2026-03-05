from __future__ import annotations

import os
import json
from typing import Any, Dict

import streamlit as st


def _build_public_storage_url(bucket: str, path: str) -> str | None:
    base = os.getenv("SUPABASE_URL", "").rstrip("/")
    if not base:
        try:
            base = (st.secrets.get("SUPABASE_URL") or "").rstrip("/")
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


def render_figuras_anexo_v(rule: Dict[str, Any]) -> None:
    figs = _extract_figures_from_rule(rule)
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

