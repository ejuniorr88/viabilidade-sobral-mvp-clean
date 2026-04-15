from __future__ import annotations

from typing import MutableMapping

from .base import arm_report_navigation_target

REPORT_GENERATED_TARGETS = {
    "report_generated_notice_context": {
        "element_id": "report-generated-context-start",
        "offset": 140,
        "behavior": "generated_context",
    },
}


def arm_report_generated_focus(session_state: MutableMapping[str, object]) -> None:
    arm_report_navigation_target(session_state, "report_generated_notice_context")
