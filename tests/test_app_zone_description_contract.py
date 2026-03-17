from pathlib import Path


def _read_app() -> str:
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    return app_path.read_text(encoding="utf-8")


def test_app_imports_or_references_zone_description_renderer():
    content = _read_app()
    assert "render_zone_description_section" in content, (
        "app.py não contém render_zone_description_section. "
        "O texto da zona pode ter sido removido da interface."
    )


def test_app_calls_zone_description_renderer_with_calc():
    content = _read_app()
    assert "render_zone_description_section(calc)" in content, (
        "app.py não chama render_zone_description_section(calc). "
        "O texto da zona pode não estar sendo renderizado."
    )
