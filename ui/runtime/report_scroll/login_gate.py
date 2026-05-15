from __future__ import annotations

from typing import Any, MutableMapping


def _next_focus_request_id(session_state: MutableMapping[str, Any]) -> int:
    try:
        current = int(session_state.get("nav_focus_request_id", 0) or 0)
    except Exception:
        current = 0
    return current + 1


def arm_login_gate_scroll(
    session_state: MutableMapping[str, Any],
    *,
    post_login_action: str | None = "calculate_viability",
) -> None:
    """Arma o scroll até o bloco de login quando a consulta exige autenticação."""

    session_state["show_login_gate"] = True
    session_state["scroll_to_login_gate"] = True
    session_state["nav_focus_target"] = "login_gate"
    session_state["nav_focus_request_id"] = _next_focus_request_id(session_state)

    if post_login_action:
        session_state["post_login_action"] = post_login_action
