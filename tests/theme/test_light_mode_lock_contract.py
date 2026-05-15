from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_streamlit_config_locks_theme_to_light_only():
    config_path = ROOT / ".streamlit" / "config.toml"
    assert config_path.exists(), ".streamlit/config.toml deve existir para travar o tema do Streamlit."

    content = config_path.read_text(encoding="utf-8").strip()
    assert content == '[theme]\nbase = "light"'


def test_theme_module_exports_only_light_mode_lock():
    init_path = ROOT / "ui" / "theme" / "__init__.py"
    content = init_path.read_text(encoding="utf-8")

    assert "from .light_mode_lock import enforce_light_mode" in content
    assert "dark_mode" not in content
    assert "inject_dark" not in content
