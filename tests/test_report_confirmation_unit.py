from __future__ import annotations

from copy import deepcopy

from core import report_confirmation as rc


def test_current_report_session_snapshot_uses_live_and_fallback_values() -> None:
    calc = {
        "lot_area_m2": 300,
        "lot_testada_m": 10,
        "lot_profundidade_m": 30,
        "built_ground_input_m2": 120,
        "area_permeavel_prevista_m2": 90,
        "lot_is_corner": False,
        "lot_is_midblock": True,
        "lot_is_irregular": False,
    }
    session_state = {
        "lot_front_m": 12,
        "lot_depth_m": 32,
        "lot_is_corner": True,
        "lot_is_midblock": False,
        "lot_is_irregular": True,
    }

    snap = rc.current_report_session_snapshot(
        calc_ref=calc,
        built_ground_value=None,
        permeable_area_value=None,
        session_state=session_state,
    )

    assert snap["lot_area_m2"] == 300.0
    assert snap["lot_front_m"] == 12.0
    assert snap["lot_depth_m"] == 32.0
    assert snap["built_ground_m2"] == 120.0
    assert snap["permeable_area_m2"] == 90.0
    assert snap["lot_is_corner"] is True
    assert snap["lot_is_midblock"] is False
    assert snap["lot_is_irregular"] is True


def test_current_report_session_snapshot_accepts_direct_input_values() -> None:
    calc = {
        "lot_area_m2": 300,
        "lot_testada_m": 10,
        "lot_profundidade_m": 30,
    }
    session_state = {}

    snap = rc.current_report_session_snapshot(
        calc_ref=calc,
        built_ground_value=150,
        permeable_area_value=80,
        session_state=session_state,
    )

    assert snap["built_ground_m2"] == 150.0
    assert snap["permeable_area_m2"] == 80.0
    assert snap["lot_front_m"] == 10.0
    assert snap["lot_depth_m"] == 30.0


def test_clear_report_runtime_state_preserve_snapshot_and_pending() -> None:
    session_state = {
        "report_unlocked": True,
        "show_inline_payments": True,
        "last_generated_pdf_bytes": b"x",
        "last_generated_pdf_signature": "sig",
        "last_saved_report_signature": "saved",
        "report_snapshot_calc": {"a": 1},
        "report_snapshot_session": {"b": 2},
        "report_snapshot_signature": "snap",
        "confirm_new_report": True,
        "pending_report_calc": {"c": 3},
        "pending_report_session": {"d": 4},
        "pending_report_signature": "pending",
        "last_calc_signature": "calc",
    }

    rc.clear_report_runtime_state(
        session_state=session_state,
        preserve_snapshot=True,
        preserve_pending=True,
    )

    assert session_state["report_unlocked"] is False
    assert session_state["show_inline_payments"] is False
    assert session_state["last_generated_pdf_bytes"] is None
    assert session_state["last_generated_pdf_signature"] is None
    assert session_state["last_saved_report_signature"] is None
    assert session_state["report_snapshot_calc"] == {"a": 1}
    assert session_state["report_snapshot_session"] == {"b": 2}
    assert session_state["report_snapshot_signature"] == "snap"
    assert session_state["confirm_new_report"] is True
    assert session_state["pending_report_signature"] == "pending"
    assert session_state["last_calc_signature"] == "calc"


def test_compute_report_confirmation_state_detects_snapshot_change() -> None:
    calc = {"use_type_code": "RES_UNI", "lot_area_m2": 300}
    session_state = {
        "report_snapshot_calc": {"old": True},
        "report_snapshot_signature": "old-signature",
        "lot_front_m": 10,
        "lot_depth_m": 30,
    }

    def fake_signature_builder(calc_ref, report_session):
        return f"{calc_ref.get('use_type_code')}|{report_session['lot_front_m']}|{report_session['lot_depth_m']}"

    state = rc.compute_report_confirmation_state(
        calc_ref=calc,
        built_ground_value=100,
        permeable_area_value=80,
        session_state=session_state,
        signature_builder=fake_signature_builder,
    )

    assert state["has_snapshot"] is True
    assert state["snapshot_signature"] == "old-signature"
    assert state["current_report_signature"] == "RES_UNI|10.0|30.0"
    assert state["is_same_as_snapshot"] is False


def test_arm_new_report_confirmation_persists_pending_payload() -> None:
    calc = {"zone": "ZAM", "use_type_code": "RES_UNI"}
    current_report_session = {"lot_area_m2": 300, "built_ground_m2": 120}
    session_state = {}

    rc.arm_new_report_confirmation(
        session_state=session_state,
        calc_ref=calc,
        current_report_session=current_report_session,
        current_report_signature="sig-123",
    )

    assert session_state["confirm_new_report"] is True
    assert session_state["pending_report_signature"] == "sig-123"
    assert session_state["pending_report_calc"] == calc
    assert session_state["pending_report_session"] == current_report_session
    assert session_state["pending_report_calc"] is not calc
    assert session_state["pending_report_session"] is not current_report_session
