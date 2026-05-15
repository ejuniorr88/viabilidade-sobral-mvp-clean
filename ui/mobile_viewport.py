from __future__ import annotations

"""Detecção leve de viewport para reorganizar o fluxo no mobile.

O Streamlit não oferece, de forma nativa, uma API Python confiável para saber a
largura da tela antes de renderizar. Este módulo usa um pequeno script no
navegador para manter o parâmetro `vf_mobile` sincronizado com o viewport,
preservando todos os demais parâmetros da URL.
"""

from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from core.auth import safe_get_query_param


MOBILE_VIEW_QUERY_KEY = "vf_mobile"
MOBILE_VIEW_STATE_KEY = "vf_mobile_view_active"


def inject_mobile_viewport_detector() -> None:
    """Injeta script que sincroniza `vf_mobile=1/0` sem apagar outros params."""

    components.html(
        """
        <script>
        (function () {
          try {
            const threshold = 768;
            const parentWindow = window.parent || window;
            const url = new URL(parentWindow.location.href);
            const isMobile = parentWindow.innerWidth <= threshold;
            const expected = isMobile ? "1" : "0";
            if (url.searchParams.get("vf_mobile") !== expected) {
              url.searchParams.set("vf_mobile", expected);
              parentWindow.location.replace(url.toString());
            }
          } catch (err) {
            // Fail silently: the desktop sidebar remains the safe fallback.
          }
        })();
        </script>
        """,
        height=0,
        width=0,
    )


def sync_mobile_viewport_state(session_state: Any) -> None:
    """Atualiza o session_state a partir do parâmetro `vf_mobile`."""

    raw_value = str(safe_get_query_param(MOBILE_VIEW_QUERY_KEY) or "").strip().lower()
    session_state[MOBILE_VIEW_STATE_KEY] = raw_value in {"1", "true", "yes", "on", "mobile"}


def is_mobile_view(session_state: Any) -> bool:
    """Retorna se o app deve usar o layout mobile inline."""

    return bool(session_state.get(MOBILE_VIEW_STATE_KEY, False))
