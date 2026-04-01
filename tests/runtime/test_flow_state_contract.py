from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='ignore')


def test_app_delegates_runtime_flags_to_new_module() -> None:
    app_py = _read(ROOT / 'app.py')

    required = [
        'from ui.runtime.flow_state import apply_post_login_runtime_flags, render_item3_scroll_if_needed',
        'apply_post_login_runtime_flags(',
        'render_item3_scroll_if_needed(',
    ]
    for item in required:
        assert item in app_py, f"app.py deixou de delegar o runtime visual para o novo módulo: {item}"



def test_runtime_module_keeps_client_area_handoff_and_item3_scroll() -> None:
    runtime_py = _read(ROOT / 'ui' / 'runtime' / 'flow_state.py')

    required = [
        'session_state.get("post_login_action") == "open_client_area"',
        'session_state["show_client_area"] = True',
        'session_state["post_login_action"] = None',
        'session_state.get("scroll_to_item3")',
        'components_module.html(',
        'getElementById("item-3-start")',
        'session_state.scroll_to_item3 = False',
    ]
    for item in required:
        assert item in runtime_py, f"ui/runtime/flow_state.py perdeu âncora crítica do runtime visual: {item}"
