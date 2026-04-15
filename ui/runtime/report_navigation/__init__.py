  from __future__ import annotations

from .confirmation import REPORT_CONFIRMATION_TARGETS, arm_report_confirmation_focus
from .generated import REPORT_GENERATED_TARGETS, arm_report_generated_focus
from .initial import REPORT_INITIAL_TARGETS, arm_report_initial_focus

REPORT_NAVIGATION_TARGETS = {
    **REPORT_INITIAL_TARGETS,
    **REPORT_CONFIRMATION_TARGETS,
    **REPORT_GENERATED_TARGETS,
}

__all__ = [
    "REPORT_NAVIGATION_TARGETS",
    "arm_report_confirmation_focus",
    "arm_report_generated_focus",
    "arm_report_initial_focus",
]
