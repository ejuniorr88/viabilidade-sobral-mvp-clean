from pathlib import Path


def _read_app() -> str:
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    return app_path.read_text(encoding="utf-8")


def test_app_keeps_minimum_section_order():
    content = _read_app()

    idx_indices = content.find("render_indices_section(")
    idx_zone_desc = content.find("render_zone_description_section(calc)")
    idx_relatorio = content.find("render_relatorio_section(calc)")

    assert idx_indices != -1, (
        "app.py não contém render_indices_section(...). "
        "A seção 4 pode ter sido removida."
    )
    assert idx_zone_desc != -1, (
        "app.py não contém render_zone_description_section(calc). "
        "A descrição da zona pode ter sido removida."
    )
    assert idx_relatorio != -1, (
        "app.py não contém render_relatorio_section(calc). "
        "O relatório urbanístico pode ter sido removido."
    )

    assert idx_indices < idx_zone_desc < idx_relatorio, (
        "A ordem mínima esperada no app.py foi quebrada. "
        "O esperado é: render_indices_section(...) "
        "antes de render_zone_description_section(calc), "
        "e esta antes de render_relatorio_section(calc)."
    )
