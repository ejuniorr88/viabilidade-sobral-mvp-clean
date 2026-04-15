from __future__ import annotations

from typing import Any, MutableMapping


def arm_report_navigation_target(session_state: MutableMapping[str, Any], target: str) -> None:
    """Arma um alvo visual do relatório sem acoplar a section.py aos detalhes do runtime."""

    request_id = int(session_state.get("nav_focus_request_id", 0) or 0) + 1
    session_state["nav_focus_request_id"] = request_id
    session_state["nav_focus_target"] = target
