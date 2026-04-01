from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_use_selector_module_keeps_expected_entrypoints() -> None:
    text = _read(ROOT / "ui" / "flow" / "use_selector.py")

    required = [
        "def render_use_selector(session_state",
        '"### 📋 1. Escolha o Uso"',
        '"### 🔎 2. Busca Direta"',
        'key="vf_categoria"',
        'key="vf_residential_option"',
        'key="vf_busca_direta"',
        'session_state.calc["use_type_code"] = selected_use_code',
        'session_state.calc["project_mode"] = "GUIA_FASE_1"',
        'session_state.calc["multi_tipo"] = selected_multi_tipo',
        'return categoria_label, selected_use_label, selected_use_code, selected_multi_tipo',
    ]
    for item in required:
        assert item in text, f"ui/flow/use_selector.py perdeu a âncora crítica: {item}"


def test_app_delegates_use_selector_instead_of_inline_sidebar_block() -> None:
    text = _read(ROOT / "app.py")

    required = [
        "from ui.flow.use_selector import render_use_selector",
        "categoria_label, selected_use_label, selected_use_code, selected_multi_tipo = render_use_selector(st.session_state)",
    ]
    for item in required:
        assert item in text, f"app.py deixou de delegar o bloco inicial de uso: {item}"

    forbidden = [
        'st.markdown("### 📋 1. Escolha o Uso")',
        'st.markdown("### 🔎 2. Busca Direta")',
        'key="vf_categoria"',
        'key="vf_residential_option"',
        'key="vf_busca_direta"',
    ]
    for item in forbidden:
        assert item not in text, f"app.py voltou a carregar inline o bloco inicial: {item}"
