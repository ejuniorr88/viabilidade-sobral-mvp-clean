from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_app_delegates_indices_section_to_new_module() -> None:
    text = _read("app.py")

    required = [
        "from ui.indices.section import render_indices_section",
        "if section4_can_try:",
        "render_indices_section(",
    ]

    for item in required:
        assert item in text, (
            "app.py deixou de delegar a seção de índices para o novo módulo: "
            f"{item}"
        )


def test_new_indices_module_exists_and_exports_render() -> None:
    init_text = _read("ui/indices/__init__.py")
    section_text = _read("ui/indices/section.py")

    assert "from .section import render_indices_section" in init_text
    assert "def render_indices_section(" in section_text
    assert 'st.header("4) Índices Urbanísticos")' in section_text
