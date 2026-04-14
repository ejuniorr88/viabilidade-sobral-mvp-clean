from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_primary_actions_module_keeps_expected_entrypoints() -> None:
    text = _read(ROOT / "ui" / "flow" / "primary_actions.py")

    required = [
        "def render_primary_actions(",
        '"🚀 GERAR CONSULTA AOS ÍNDICES URBANÍSTICOS"',
        '"🗑️ LIMPAR TUDO"',
        'session_state.calc = {"use_type_code": session_state.calc.get("use_type_code", "RES_UNI")}',
        "clear_report_runtime_state(clear_last_calc_signature=True)",
        "st.rerun()",
        "return clicked_calcular",
    ]
    for item in required:
        assert item in text, f"ui/flow/primary_actions.py perdeu a âncora crítica: {item}"


def test_app_delegates_primary_actions_instead_of_inline_buttons() -> None:
    text = _read(ROOT / "app.py")

    required = [
        "from ui.flow.primary_actions import render_primary_actions",
        "clicked_calcular = render_primary_actions(",
        "clear_report_runtime_state=_clear_report_runtime_state",
    ]
    for item in required:
        assert item in text, f"app.py deixou de delegar o bloco principal de ações: {item}"

    assert 'st.button(\n        "🚀 GERAR CONSULTA AOS ÍNDICES URBANÍSTICOS"' not in text
    assert 'st.button(\n        "🗑️ LIMPAR TUDO"' not in text
