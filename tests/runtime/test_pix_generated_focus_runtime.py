from __future__ import annotations

from ui.runtime.pix_generated_focus import (
    arm_pix_generated_focus,
    clear_pix_generated_focus_state,
    should_schedule_pending_resume_once,
    should_skip_pending_auto_refresh_once,
)


def test_pix_generated_focus_skip_and_resume_flags_are_one_shot() -> None:
    session_state = {}

    arm_pix_generated_focus(session_state, payment_id="pay_123")

    assert session_state["nav_focus_target"] == "pix_generated"
    assert should_skip_pending_auto_refresh_once(session_state, "pay_123") is True
    assert should_skip_pending_auto_refresh_once(session_state, "pay_123") is False
    assert should_schedule_pending_resume_once(session_state, "pay_123") is True
    assert should_schedule_pending_resume_once(session_state, "pay_123") is False


def test_pix_generated_focus_state_can_be_cleared() -> None:
    session_state = {}

    arm_pix_generated_focus(session_state, payment_id="pay_123")
    clear_pix_generated_focus_state(session_state, payment_id="pay_123")

    assert "pix_generated_focus_payment_id" not in session_state
    assert "pix_generated_skip_auto_refresh_once" not in session_state
    assert "pix_generated_resume_auto_refresh_once" not in session_state
