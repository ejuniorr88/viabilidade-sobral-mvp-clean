from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_map_section_bridges_to_consolidated_map_module() -> None:
    text = _read(ROOT / "ui" / "map" / "section.py")

    required = [
        "from ui.mapa import render_mapa_section as _render_mapa_core",
        "def render_mapa_section(zones_gj",
        "return _render_mapa_core(zones_gj)",
        "def render_map_section(zones_gj",
        "return render_mapa_section(zones_gj)",
    ]
    for item in required:
        assert item in text, f"ui/map/section.py perdeu a ponte estrutural com o módulo consolidado do mapa: {item}"


def test_consolidated_map_module_keeps_component_bridge() -> None:
    text = _read(ROOT / "ui" / "mapa.py")

    required = [
        "from streamlit_folium import st_folium",
        "from components.google_map_component import render_google_map",
        "def _render_google_map_section(",
        'key="google_map_section_main"',
    ]
    for item in required:
        assert item in text, f"ui/mapa.py perdeu a ponte estrutural do componente do mapa: {item}"
