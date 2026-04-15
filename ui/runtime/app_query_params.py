from __future__ import annotations

import re
import unicodedata
from typing import Any, Optional

import streamlit as st

from core.auth import safe_get_query_param
from core.state_helpers import clear_all_checkout_states


def normalize_checkout_plan_slug(value: Any) -> Optional[str]:
    raw = str(value or "").strip()
    if not raw:
        return None

    normalized = unicodedata.normalize("NFD", raw)
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized.lower()).strip("_")

    if "intermedi" in normalized:
        return "intermediario"
    if "profissional" in normalized:
        return "profissional"
    if "basico" in normalized:
        return "basico"
    return normalized or None


def clear_landing_checkout_query_params() -> None:
    keys = ["checkout", "plan"]
    try:
        for key in keys:
            try:
                del st.query_params[key]
            except Exception:
                pass
    except Exception:
        try:
            current = st.experimental_get_query_params()
            cleaned = {k: v for k, v in current.items() if k not in keys}
            st.experimental_set_query_params(**cleaned)
        except Exception:
            pass


def clear_home_nav_query_param() -> None:
    try:
        try:
            del st.query_params["nav"]
        except Exception:
            pass
    except Exception:
        try:
            current = st.experimental_get_query_params()
            cleaned = {k: v for k, v in current.items() if k != "nav"}
            st.experimental_set_query_params(**cleaned)
        except Exception:
            pass


def consume_home_nav_query_param(session_state) -> None:
    nav_value = str(safe_get_query_param("nav") or "").strip().lower()
    if nav_value != "home":
        return

    session_state["show_plans_page"] = False
    session_state["show_client_area"] = False
    session_state["post_login_action"] = None
    clear_all_checkout_states()
    clear_home_nav_query_param()


def consume_landing_checkout_query_params(session_state) -> None:
    checkout_flag = str(safe_get_query_param("checkout") or "").strip().lower()
    plan_value = safe_get_query_param("plan")
    should_open_checkout = checkout_flag in {"1", "true", "yes", "on"} or bool(plan_value)

    if not should_open_checkout:
        return

    session_state["landing_checkout_mode"] = True
    session_state["landing_selected_plan_slug"] = normalize_checkout_plan_slug(plan_value)
    session_state["show_plans_page"] = True
    session_state["show_client_area"] = False

    if not session_state.get("auth_logged_in"):
        session_state["post_login_action"] = "open_plans_page"

    clear_landing_checkout_query_params()
