from __future__ import annotations

from typing import MutableMapping, Any


def bootstrap_session_state(session_state: MutableMapping[str, Any]) -> None:
    if "calc" not in session_state or not isinstance(session_state.get("calc"), dict):
        session_state["calc"] = {}

    defaults = {
        "last_calc_signature": None,
        "confirm_new_report": False,
        "free_calc_done": False,
        "show_login_gate": False,
        "scroll_to_login_gate": False,
        "scroll_to_item3": False,
        "post_login_action": None,
        "show_inline_payments": False,
        "show_client_area": False,
    }

    for key, value in defaults.items():
        session_state.setdefault(key, value)
