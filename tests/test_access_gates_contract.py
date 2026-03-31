from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_access_gates_contract_keeps_client_area_and_login_gate_anchors() -> None:
    access_gates = _read(ROOT / "ui" / "access_gates.py")

    required = [
        'def render_login_gate_block()',
        'def render_client_area_gate(',
        'def resolve_calculate_access(',
        'def render_login_gate_if_needed(',
        'render_google_login_box(',
        'render_client_area_page(',
        'st.markdown("## Área do cliente")',
        'st.info("Faça login com Google para acessar sua área do cliente e ver seus relatórios salvos.")',
        'session_state["post_login_action"] = "calculate_viability"',
        'session_state["show_login_gate"] = False',
        'session_state["scroll_to_item3"] = True',
        'st.divider()',
    ]
    for item in required:
        assert item in access_gates, f"Arquivo ui/access_gates.py perdeu a âncora crítica: {item}"


def test_app_delegates_access_gates_instead_of_inline_logic() -> None:
    app_py = _read(ROOT / "app.py")

    required = [
        'from ui.access_gates import (',
        'render_login_gate_block,',
        'render_client_area_gate,',
        'resolve_calculate_access,',
        'render_login_gate_if_needed,',
        'render_client_area_gate(',
        'run_free_calc_now = resolve_calculate_access(',
        'render_login_gate_if_needed(',
    ]
    for item in required:
        assert item in app_py, f"app.py deixou de delegar o gate de acesso esperado: {item}"
