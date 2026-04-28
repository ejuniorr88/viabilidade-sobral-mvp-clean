from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIGHT_LOCK = ROOT / "ui" / "theme" / "light_mode_lock.py"


def test_light_mode_lock_is_narrow_and_does_not_style_app_elements():
    content = LIGHT_LOCK.read_text(encoding="utf-8")

    required = [
        "def enforce_light_mode()",
        "color-scheme: light",
        'data-theme", "light"',
    ]
    for token in required:
        assert token in content

    forbidden_tokens = [
        "overflow-y",
        "scrollbar",
        "stButton",
        "button[kind",
        "button:hover",
        "section[data-testid=\"stSidebar\"]",
        ".vf-primary-button",
        ".vf-report-action",
        "MutationObserver",
        "background-color:",
        "color:",
    ]
    for token in forbidden_tokens:
        assert token not in content


def test_light_mode_lock_does_not_import_app_shell_or_sensitive_modules():
    content = LIGHT_LOCK.read_text(encoding="utf-8")

    forbidden_imports = [
        "ui.app_shell",
        "core.auth",
        "core.credits",
        "core.checkout_flow",
        "core.client_reports",
        "core.payments",
        "core.zone_resolution",
    ]
    for token in forbidden_imports:
        assert token not in content
