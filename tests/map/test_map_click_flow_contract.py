from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_map_module_keeps_click_capture_and_rerun_flow() -> None:
    text = _read(ROOT / "ui" / "mapa.py")

    required = [
        "def _apply_click_update(",
        'st.session_state[state_key_last_click] = {"lat": new_lat, "lon": new_lon}',
        'st.session_state[state_key_click_hash] = new_hash',
        'calc["_click_hash"] = new_hash',
        'if out and out.get("last_clicked"):',
        'new_lat = float(out["last_clicked"]["lat"])',
        'new_lon = float(out["last_clicked"]["lng"])',
        "st.rerun()",
    ]
    for item in required:
        assert item in text, f"ui/mapa.py perdeu uma âncora crítica do fluxo de clique do mapa: {item}"


def test_map_module_keeps_selected_coordinates_feedback() -> None:
    text = _read(ROOT / "ui" / "mapa.py")

    required = [
        'if st.session_state.get(state_key_last_click):',
        '📍 Coordenadas selecionadas:',
        "lat {st.session_state[state_key_last_click]['lat']:.6f}",
        "lon {st.session_state[state_key_last_click]['lon']:.6f}",
    ]
    for item in required:
        assert item in text, f"ui/mapa.py perdeu o feedback visual das coordenadas selecionadas: {item}"
