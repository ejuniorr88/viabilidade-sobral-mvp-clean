from pathlib import Path
import re


def _read_app() -> str:
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    return app_path.read_text(encoding="utf-8")


def _find_first_call(content: str, func_name: str) -> int:
    match = re.search(rf"\b{re.escape(func_name)}\s*\(", content)
    return -1 if match is None else match.start()



def test_app_keeps_minimum_section_order():
    content = _read_app()

    idx_indices = _find_first_call(content, "render_indices_section")
    idx_zone_desc = _find_first_call(content, "render_zone_description_section")
    idx_relatorio = _find_first_call(content, "render_relatorio_section")

    assert idx_indices != -1, (
        "app.py não contém render_indices_section(...). "
        "A seção 4 pode ter sido removida."
    )
    assert idx_zone_desc != -1, (
        "app.py não contém render_zone_description_section(...). "
        "A descrição da zona pode ter sido removida."
    )
    assert idx_relatorio != -1, (
        "app.py não contém render_relatorio_section(...). "
        "O relatório urbanístico pode ter sido removido."
    )

    assert idx_indices < idx_zone_desc < idx_relatorio, (
        "A ordem mínima esperada no app.py foi quebrada. "
        "O esperado é: render_indices_section(...) "
        "antes de render_zone_description_section(...), "
        "e esta antes de render_relatorio_section(...)."
    )
