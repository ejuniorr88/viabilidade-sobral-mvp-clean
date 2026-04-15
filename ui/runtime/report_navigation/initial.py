from __future__ import annotations

from typing import MutableMapping

from .base import arm_report_navigation_target

REPORT_INITIAL_TARGETS = {
    "report_initial_section": {
        "element_id": "report-section-start",
        "offset": 0,
        "behavior": "initial",
    },
}


def arm_report_initial_focus(session_state: MutableMapping[str, object]) -> None:
    arm_report_navigation_target(session_state, "report_initial_section")
