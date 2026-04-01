from __future__ import annotations

from typing import Any, MutableMapping, Optional


def apply_post_login_runtime_flags(
    session_state: MutableMapping[str, Any],
    *,
    user_logged_in: bool,
    user_id: Optional[str],
) -> None:
    """Resolve flags visuais do topo após login sem reabrir auth profunda.

    Mantém o mesmo comportamento consolidado do app: quando a ação pendente
    é abrir a Área do cliente, a flag visual é armada e a ação pendente é limpa.
    """

    if session_state.get("post_login_action") == "open_client_area" and user_logged_in and user_id:
        session_state["show_client_area"] = True
        session_state["post_login_action"] = None


def render_item3_scroll_if_needed(*, session_state: MutableMapping[str, Any], components_module: Any) -> None:
    """Executa o scroll visual até o item 3 e limpa a flag consolidada."""

    if session_state.get("scroll_to_item3"):
        components_module.html(
            """
            <script>
                const rootDoc = window.parent.document;
                const el = rootDoc.getElementById("item-3-start");
                if (el) {
                    el.scrollIntoView({ behavior: "smooth", block: "start" });
                }
            </script>
            """,
            height=0,
        )
        session_state.scroll_to_item3 = False
