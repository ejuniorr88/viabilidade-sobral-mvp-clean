from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_map_section_module_keeps_expected_entrypoints() -> None:
    text = _read(ROOT / "ui" / "map" / "section.py")

    required = [
        "from ui.mapa import render_mapa_section as _render_mapa_core",
        "def render_mapa_section(zones_gj",
        "📍 Selecione o lote no mapa:",
        "return _render_mapa_core(zones_gj)",
        "def render_map_section(zones_gj",
        "return render_mapa_section(zones_gj)",
    ]
    for item in required:
        assert item in text, f"ui/map/section.py perdeu a âncora crítica: {item}"



def test_app_delegates_map_section_to_new_module() -> None:
    text = _read(ROOT / "app.py")

    required = [
        "from ui.map.section import render_mapa_section",
        "radius_m = render_mapa_section(zones_gj)",
    ]
    for item in required:
        assert item in text, f"app.py deixou de delegar a seção do mapa para o novo módulo: {item}"

    assert "📍 Selecione o lote no mapa:" not in text
