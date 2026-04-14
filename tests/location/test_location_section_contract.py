from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_location_section_module_keeps_expected_entrypoints() -> None:
    text = _read(ROOT / "ui" / "location" / "section.py")

    required = [
        "from ui.app_shell import card as _card",
        "def render_localizacao_section(*args, **kwargs)",
        'st.subheader("3) Localização (zona + via)")',
        '_card("Zona", zone)',
        '_card("Rua / Logradouro", via_nome)',
        "def render_location_section(*args, **kwargs)",
        "return render_localizacao_section(*args, **kwargs)",
    ]
    for item in required:
        assert item in text, f"ui/location/section.py perdeu a âncora crítica: {item}"



def test_app_delegates_location_section_to_new_module() -> None:
    text = _read(ROOT / "app.py")

    required = [
        "from ui.location.section import render_localizacao_section",
        "render_localizacao_section(True, zones_prepared, radius_m)",
        "render_localizacao_section(False, zones_prepared, radius_m)",
    ]
    for item in required:
        assert item in text, f"app.py deixou de delegar a seção de localização para o novo módulo: {item}"

    assert "from ui.localizacao import render_localizacao_section" not in text
