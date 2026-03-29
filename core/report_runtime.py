from __future__ import annotations

from typing import Any, MutableMapping


def current_report_session_snapshot(*, calc_ref, built_ground_value, permeable_area_value, session_state: MutableMapping[str, Any]):
    return {
        "lot_area_m2": calc_ref.get("lot_area_m2"),
        "built_ground_m2": built_ground_value,
        "permeable_area_m2": permeable_area_value,
        "lot_front_m": calc_ref.get("lot_front_m"),
        "lot_depth_m": calc_ref.get("lot_depth_m"),
        "lot_is_corner": calc_ref.get("lot_is_corner"),
        "lot_is_midblock": calc_ref.get("lot_is_midblock"),
        "lot_is_irregular": bool(session_state.get("lot_is_irregular", False)),
    }


def commit_report_snapshot(*, calc_ref, session_snapshot, pdf_bytes, signature, session_state: MutableMapping[str, Any], deepcopy_func):
    session_state["report_snapshot_calc"] = deepcopy_func(calc_ref)
    session_state["report_snapshot_session"] = deepcopy_func(session_snapshot)
    session_state["report_snapshot_signature"] = signature
    session_state["last_generated_pdf_bytes"] = pdf_bytes
    session_state["last_generated_pdf_signature"] = signature
    session_state["report_unlocked"] = True
    session_state["show_inline_payments"] = False


def clear_pending_report(session_state: MutableMapping[str, Any]) -> None:
    session_state["confirm_new_report"] = False
    session_state["pending_report_calc"] = None
    session_state["pending_report_session"] = None
    session_state["pending_report_signature"] = None


def clear_report_runtime_state(session_state: MutableMapping[str, Any], *, clear_last_calc_signature: bool = False) -> None:
    session_state["report_unlocked"] = False
    session_state["show_inline_payments"] = False
    session_state["last_generated_pdf_bytes"] = None
    session_state["last_generated_pdf_signature"] = None
    session_state["last_saved_report_signature"] = None
    session_state["report_snapshot_calc"] = None
    session_state["report_snapshot_session"] = None
    session_state["report_snapshot_signature"] = None
    clear_pending_report(session_state)
    if clear_last_calc_signature:
        session_state["last_calc_signature"] = None
