from pathlib import Path


def _read_app() -> str:
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    return app_path.read_text(encoding="utf-8")


def test_app_imports_or_references_relatorio_renderer():
    content = _read_app()
    assert "render_relatorio_section" in content, (
        "app.py não contém render_relatorio_section. "
        "O relatório urbanístico pode ter sido removido da interface."
    )


def test_app_calls_relatorio_renderer_with_calc():
    content = _read_app()
    assert "render_relatorio_section(calc)" in content, (
        "app.py não chama render_relatorio_section(calc). "
        "O relatório urbanístico pode não estar sendo renderizado."
    )
