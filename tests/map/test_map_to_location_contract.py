from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_app_keeps_map_to_location_flow_contract() -> None:
    app_text = _read(ROOT / "app.py")

    required = [
        "radius_m = render_mapa_section(zones_gj)",
        "_ = render_localizacao_section(True, zones_prepared, radius_m)",
        "_ = render_localizacao_section(False, zones_prepared, radius_m)",
    ]
    for item in required:
        assert item in app_text, f"app.py perdeu a passagem estrutural do mapa para localização: {item}"


def test_location_section_keeps_map_dependent_inputs() -> None:
    text = _read(ROOT / "ui" / "location" / "section.py")

    required = [
        "def _coerce_call(args, kwargs)",
        'render_localizacao_section(calcular, zones_prepared, radius_m)',
        'if not getattr(st.session_state, "last_click", None):',
        'lat = st.session_state.last_click["lat"]',
        'lon = st.session_state.last_click["lon"]',
        'calc["radius_m"] = int(radius_m)',
        "find_street(lat=lat, lon=lon, radius_m=float(radius_m))",
    ]
    for item in required:
        assert item in text, f"ui/location/section.py perdeu a dependência estrutural do clique do mapa: {item}"
