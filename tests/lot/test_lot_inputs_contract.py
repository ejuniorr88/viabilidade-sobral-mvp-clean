from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_lot_inputs_module_keeps_expected_entrypoint() -> None:
    text = _read(ROOT / "ui" / "lot" / "inputs.py")

    assert "from ui.lote import render_lote_section" in text
    assert "def render_lot_inputs():" in text
    assert "return render_lote_section()" in text


def test_app_delegates_lot_inputs_to_ui_lot_module() -> None:
    text = _read(ROOT / "app.py")

    assert "from ui.lot.inputs import render_lot_inputs" in text
    assert "lot_area, built_ground, permeable_area = render_lot_inputs()" in text
    assert "render_lote_section()" not in text
