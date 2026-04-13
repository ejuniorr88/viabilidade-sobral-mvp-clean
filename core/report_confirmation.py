from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Callable, Dict, MutableMapping


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def current_report_session_snapshot(
    *,
    calc_ref: Dict[str, Any],
    built_ground_value: Any,
    permeable_area_value: Any,
    session_state: MutableMapping[str, Any],
) -> Dict[str, Any]:
    lot_front_live = _safe_float(
        session_state.get("lot_front_m")
        or calc_ref.get("lot_front_m")
        or calc_ref.get("lot_testada_m")
        or 0.0
    )
    lot_depth_live = _safe_float(
        session_state.get("lot_depth_m")
        or calc_ref.get("lot_depth_m")
        or calc_ref.get("lot_profundidade_m")
        or 0.0
    )
    lot_area_live = _safe_float(calc_ref.get("lot_area_m2") or 0.0)
    built_ground_live = _safe_float(
        built_ground_value
        if built_ground_value is not None
        else (calc_ref.get("built_ground_m2") or calc_ref.get("built_ground_input_m2") or 0.0)
    )
    permeable_area_live = _safe_float(
        permeable_area_value
        if permeable_area_value is not None
        else (calc_ref.get("area_permeavel_prevista_m2") or calc_ref.get("permeable_area_m2") or 0.0)
    )
    lot_is_corner_live = bool(session_state.get("lot_is_corner", calc_ref.get("lot_is_corner", False)))
    lot_is_midblock_live = bool(
        session_state.get("lot_is_midblock", calc_ref.get("lot_is_midblock", not lot_is_corner_live))
    )
    lot_is_irregular_live = bool(
        session_state.get("lot_is_irregular", calc_ref.get("lot_irregular", calc_ref.get("lot_is_irregular", False)))
    )
    return {
        "lot_area_m2": lot_area_live,
        "built_ground_m2": built_ground_live,
        "permeable_area_m2": permeable_area_live,
        "lot_front_m": lot_front_live,
        "lot_depth_m": lot_depth_live,
        "lot_is_corner": lot_is_corner_live,
        "lot_is_midblock": lot_is_midblock_live,
        "lot_is_irregular": lot_is_irregular_live,
    }


def commit_report_snapshot(
    *,
    session_state: MutableMapping[str, Any],
    calc_ref: Dict[str, Any],
    session_snapshot: Dict[str, Any],
    pdf_bytes: bytes,
    signature: str,
) -> None:
    session_state["report_snapshot_calc"] = deepcopy(calc_ref)
    session_state["report_snapshot_session"] = deepcopy(session_snapshot)
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
    session_state["report_review_open"] = False


def clear_report_runtime_state(
    *,
    session_state: MutableMapping[str, Any],
    clear_last_calc_signature: bool = False,
    preserve_snapshot: bool = False,
    preserve_pending: bool = False,
) -> None:
    session_state["report_unlocked"] = False
    session_state["show_inline_payments"] = False
    session_state["last_generated_pdf_bytes"] = None
    session_state["last_generated_pdf_signature"] = None
    session_state["last_saved_report_signature"] = None
    if not preserve_snapshot:
        session_state["report_snapshot_calc"] = None
        session_state["report_snapshot_session"] = None
        session_state["report_snapshot_signature"] = None
    if not preserve_pending:
        clear_pending_report(session_state)
    if clear_last_calc_signature:
        session_state["last_calc_signature"] = None


def build_calc_signature(
    *,
    selected_lat: Any,
    selected_lon: Any,
    use_type_code: Any,
    project_mode: Any,
    categoria_label: Any,
    lot_area_m2: Any = None,
    built_ground_m2: Any = None,
    permeable_area_m2: Any = None,
    lot_front_m: Any = None,
    lot_depth_m: Any = None,
    lot_is_corner: Any = None,
    lot_is_midblock: Any = None,
    lot_is_irregular: Any = None,
) -> str:
    return json.dumps(
        {
            "lat": selected_lat,
            "lon": selected_lon,
            "use_type_code": use_type_code,
            "project_mode": project_mode,
            "categoria_label": categoria_label,
            "lot_area_m2": _safe_float(lot_area_m2),
            "built_ground_m2": _safe_float(built_ground_m2),
            "permeable_area_m2": _safe_float(permeable_area_m2),
            "lot_front_m": _safe_float(lot_front_m),
            "lot_depth_m": _safe_float(lot_depth_m),
            "lot_is_corner": bool(lot_is_corner),
            "lot_is_midblock": bool(lot_is_midblock),
            "lot_is_irregular": bool(lot_is_irregular),
        },
        sort_keys=True,
        default=str,
    )


def compute_report_confirmation_state(
    *,
    calc_ref: Dict[str, Any],
    built_ground_value: Any,
    permeable_area_value: Any,
    session_state: MutableMapping[str, Any],
    signature_builder: Callable[[Dict[str, Any], Dict[str, Any]], str],
) -> Dict[str, Any]:
    current_report_session = current_report_session_snapshot(
        calc_ref=calc_ref,
        built_ground_value=built_ground_value,
        permeable_area_value=permeable_area_value,
        session_state=session_state,
    )
    current_report_signature = signature_builder(calc_ref, current_report_session)
    snapshot_signature = session_state.get("report_snapshot_signature")
    has_snapshot = bool(session_state.get("report_snapshot_calc")) and bool(snapshot_signature)
    is_same_as_snapshot = bool(has_snapshot and snapshot_signature == current_report_signature)
    return {
        "current_report_session": current_report_session,
        "current_report_signature": current_report_signature,
        "snapshot_signature": snapshot_signature,
        "has_snapshot": has_snapshot,
        "is_same_as_snapshot": is_same_as_snapshot,
    }


def arm_new_report_confirmation(
    *,
    session_state: MutableMapping[str, Any],
    calc_ref: Dict[str, Any],
    current_report_session: Dict[str, Any],
    current_report_signature: str,
) -> None:
    session_state["confirm_new_report"] = True
    session_state["pending_report_calc"] = deepcopy(calc_ref)
    session_state["pending_report_session"] = deepcopy(current_report_session)
    session_state["pending_report_signature"] = current_report_signature


def arm_report_review(
    *,
    session_state: MutableMapping[str, Any],
    calc_ref: Dict[str, Any],
    current_report_session: Dict[str, Any],
    current_report_signature: str,
    requires_new_credit: bool,
) -> None:
    clear_pending_report(session_state)
    session_state["report_review_open"] = True
    session_state["pending_report_calc"] = deepcopy(calc_ref)
    session_state["pending_report_session"] = deepcopy(current_report_session)
    session_state["pending_report_signature"] = current_report_signature
    if requires_new_credit:
        session_state["confirm_new_report"] = True


def should_reset_pending_review(
    *,
    session_state: MutableMapping[str, Any],
    current_report_signature: str,
) -> bool:
    pending_signature = session_state.get("pending_report_signature")
    review_open = bool(session_state.get("report_review_open"))
    if not review_open or not pending_signature:
        return False
    return str(pending_signature) != str(current_report_signature)
