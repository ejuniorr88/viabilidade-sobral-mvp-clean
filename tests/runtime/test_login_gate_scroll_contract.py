from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_login_gate_helper_sets_focus_flags() -> None:
    src = _read("ui/runtime/report_scroll/login_gate.py")
    tree = ast.parse(src)
    assert "def arm_login_gate_scroll" in src
    assert '"show_login_gate"' in src
    assert '"scroll_to_login_gate"' in src
    assert '"nav_focus_target"' in src
    assert '"login_gate"' in src
    assert '"post_login_action"' in src


def test_guest_calculate_path_arms_login_scroll_and_reruns() -> None:
    src = _read("ui/access_gates.py")
    assert "from ui.runtime.report_scroll.login_gate import arm_login_gate_scroll" in src
    assert 'arm_login_gate_scroll(session_state, post_login_action="calculate_viability")' in src
    assert "st.rerun()" in src


def test_login_gate_uses_robust_scroll_behavior() -> None:
    src = _read("ui/runtime/navigation_focus.py")
    assert '"login_gate": {"element_id": "login-gate-start", "offset": 0, "behavior": "login_gate"}' in src
    assert "usesRobustScroll" in src
    assert "'login_gate'" in src
    assert "const useElementFirst = behavior === 'confirmation' || behavior === 'initial' || usesRobustScroll;" in src
