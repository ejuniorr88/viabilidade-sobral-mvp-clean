from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXCLUDED_DIRS = {".git", ".venv", "venv", "__pycache__", "tests", "backup"}


def _project_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        yield path


def test_old_dark_mode_module_is_not_present():
    assert not (ROOT / "ui" / "theme" / "dark_mode.py").exists(), (
        "Remova ui/theme/dark_mode.py. O sistema foi travado em modo claro e "
        "não deve manter o módulo antigo de correção de dark mode."
    )


def test_project_code_does_not_import_old_dark_mode_helpers():
    forbidden = [
        "from ui.theme.dark_mode",
        "import ui.theme.dark_mode",
        "inject_dark_mode_text_fixes",
    ]

    offenders = []
    for path in _project_files():
        if path.suffix not in {".py", ".toml", ".md"}:
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for token in forbidden:
            if token in content:
                offenders.append(f"{path.relative_to(ROOT)} contém {token}")

    assert not offenders, "Referências antigas ao dark mode encontradas: " + "; ".join(offenders)
