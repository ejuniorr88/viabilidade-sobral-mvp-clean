from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_app_does_not_revert_to_legacy_map_rendering_directly() -> None:
    text = _read(ROOT / "app.py")

    assert "from ui.mapa import render_mapa_section" not in text, "app.py voltou a importar o módulo legado do mapa diretamente."
    assert "st_folium(" not in text, "app.py voltou a renderizar o mapa diretamente."
    assert "render_google_map(" not in text, "app.py voltou a acoplar o componente do mapa diretamente."
    assert "from ui.map.section import render_mapa_section" in text, "app.py perdeu a delegação do mapa para ui/map/section.py."


def test_new_map_module_and_legacy_core_both_exist() -> None:
    assert (ROOT / "ui" / "map" / "section.py").exists(), "ui/map/section.py não existe."
    assert (ROOT / "ui" / "mapa.py").exists(), "ui/mapa.py não existe."
