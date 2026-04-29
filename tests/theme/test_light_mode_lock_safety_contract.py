from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_light_mode_lock_is_narrow_and_does_not_style_app_elements() -> None:
    module_path = ROOT / "ui" / "theme" / "light_mode_lock.py"
    assert module_path.exists(), "ui/theme/light_mode_lock.py não encontrado"

    text = module_path.read_text(encoding="utf-8", errors="ignore")
    css_and_js = text.lower()

    assert "color-scheme: light" in css_and_js
    assert "data-theme" in css_and_js
    assert "streamlit:theme" in css_and_js

    forbidden_style_selectors = [
        "::-webkit-scrollbar",
        "stbutton",
        "stsidebar",
        "sthorizontalblock",
        "vf-brand",
        "vf-nav",
        "background:",
        "color:",
        "border:",
        "box-shadow",
    ]
    for item in forbidden_style_selectors:
        assert item not in css_and_js, (
            "O bloqueio de modo claro deve continuar estreito e não pode estilizar "
            f"elementos visuais do app: {item}"
        )
