from __future__ import annotations

from typing import Any, MutableMapping


def bootstrap_session_state(session_state: MutableMapping[str, Any]) -> None:
    if "calc" not in session_state or not isinstance(session_state.get("calc"), dict):
        session_state["calc"] = {}

    session_state.setdefault("last_calc_signature", None)
    session_state.setdefault("confirm_new_report", False)
    session_state.setdefault("report_review_open", False)
    session_state.setdefault("free_calc_done", False)
    session_state.setdefault("show_login_gate", False)
    session_state.setdefault("scroll_to_login_gate", False)
    session_state.setdefault("scroll_to_item3", False)
    session_state.setdefault("post_login_action", None)
    session_state.setdefault("show_inline_payments", False)
    session_state.setdefault("show_client_area", False)
