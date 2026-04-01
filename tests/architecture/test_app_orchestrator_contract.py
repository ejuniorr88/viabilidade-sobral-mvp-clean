from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_app_py_keeps_orchestrator_import_contract() -> None:
    text = _read(ROOT / "app.py")

    required_imports = [
        "from core.session.bootstrap import bootstrap_session_state",
        "from ui.flow.use_selector import render_use_selector",
        "from ui.lot.inputs import render_lot_inputs",
        "from ui.map.section import render_mapa_section",
        "from ui.location.section import render_localizacao_section",
        "from ui.indices.section import render_indices_section",
        "from ui.analysis.section import render_analise_section",
        "from ui.report.section import render_report_section",
        "from ui.runtime.flow_state import apply_post_login_runtime_flags, render_item3_scroll_if_needed",
    ]
    for item in required_imports:
        assert item in text, f"app.py perdeu o import estrutural do orquestrador: {item}"

    forbidden_legacy_imports = [
        "from ui.mapa import render_mapa_section",
        "from ui.localizacao import render_localizacao_section",
        "from ui.indices import render_indices_section",
        "from ui.analise import render_analise_section",
    ]
    for item in forbidden_legacy_imports:
        assert item not in text, f"app.py voltou a importar a seção antiga diretamente: {item}"


def test_app_py_does_not_recreate_local_section_renderers() -> None:
    text = _read(ROOT / "app.py")

    forbidden_local_defs = [
        "def render_use_selector(",
        "def render_lot_inputs(",
        "def render_mapa_section(",
        "def render_localizacao_section(",
        "def render_indices_section(",
        "def render_analise_section(",
        "def render_report_section(",
        "def apply_post_login_runtime_flags(",
        "def render_item3_scroll_if_needed(",
    ]
    for item in forbidden_local_defs:
        assert item not in text, f"app.py voltou a recriar internamente um bloco já modularizado: {item}"
