from __future__ import annotations

"""Constantes isoladas para scroll automático em mobile.

Este módulo só padroniza nomes e tempos usados pelos scripts visuais
de scroll para evitar disputa entre âncoras no celular.
"""

MOBILE_SCROLL_GUARD_KEY = "__viabilidade_mobile_scroll_guard__"
MOBILE_SCROLL_COOLDOWN_MS = 1800
MOBILE_SCROLL_SETTLE_DELAY_MS = 760
MOBILE_SCROLL_RETRY_DELAY_MS = 1180

__all__ = [
    "MOBILE_SCROLL_GUARD_KEY",
    "MOBILE_SCROLL_COOLDOWN_MS",
    "MOBILE_SCROLL_SETTLE_DELAY_MS",
    "MOBILE_SCROLL_RETRY_DELAY_MS",
]
