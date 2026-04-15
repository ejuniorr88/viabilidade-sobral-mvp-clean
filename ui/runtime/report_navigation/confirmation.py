from __future__ import annotations

from typing import MutableMapping

from .base import arm_report_navigation_target

REPORT_CONFIRMATION_TARGETS = {
    "report_confirmation_block": {
        "element_id": "report-review-confirm-start",
        "offset": 0,
        "behavior": "confirmation",
    },
}


def arm_report_confirmation_focus(session_state: MutableMapping[str, object]) -> None:
    arm_report_navigation_target(session_state, "report_confirmation_block")
