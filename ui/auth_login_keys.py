from __future__ import annotations

import re


def _slugify(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "default"


def build_auth_popup_key(
    *,
    context: str,
    label: str,
    subtle: bool,
    force_select_account: bool,
) -> str:
    """
    Gera uma key única e estável por contexto de renderização do login.

    Isso evita colisões do componente de popup quando o CTA de login aparece
    em mais de um ponto ao mesmo tempo (ex.: topo + gate).
    """
    context_slug = _slugify(context)
    label_slug = _slugify(label)
    mode = "subtle" if subtle else "main"
    intent = "swap" if force_select_account else "login"
    return f"auth_google_{context_slug}_{mode}_{intent}_{label_slug}"
