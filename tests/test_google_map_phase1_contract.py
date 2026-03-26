from pathlib import Path


def test_ui_mapa_supports_google_provider_contract():
    src = Path("ui/mapa.py").read_text(encoding="utf-8")
    assert "MAP_PROVIDER" in src
    assert "GOOGLE_MAPS_API_KEY" in src
    assert "render_google_map" in src
    assert "voltar automaticamente para o mapa atual" in src or "Voltando ao mapa atual" in src


def test_google_component_wrapper_contract():
    src = Path("components/google_map_component/__init__.py").read_text(encoding="utf-8")
    assert "declare_component" in src
    assert "zones_geojson" in src
    assert "radius_m" in src
    assert "google_map_component" in src
