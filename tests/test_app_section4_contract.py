from pathlib import Path


def _read_app() -> str:
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    return app_path.read_text(encoding="utf-8")


def test_app_imports_render_indices_section():
    content = _read_app()
    assert "render_indices_section" in content, (
        "app.py não contém render_indices_section. "
        "A seção 4 pode ter sido removida por acidente."
    )


def test_section4_gate_still_exists():
    content = _read_app()
    assert "section4_can_try" in content, (
        "app.py não contém a variável/condição section4_can_try. "
        "O gate da seção 4 pode ter sido alterado indevidamente."
    )
    assert "if section4_can_try:" in content, (
        "app.py não contém o bloco 'if section4_can_try:'. "
        "A renderização protegida da seção 4 pode ter sido removida."
    )


def test_render_indices_section_is_called_inside_section4_block():
    content = _read_app()

    marker = "if section4_can_try:"
    idx = content.find(marker)

    assert idx != -1, (
        "Não foi encontrado o bloco 'if section4_can_try:' em app.py."
    )

    tail = content[idx:]
    next_top_level_header = tail.find("\n# ")
    block = tail if next_top_level_header == -1 else tail[:next_top_level_header]

    assert "render_indices_section(" in block, (
        "A chamada render_indices_section(...) não está dentro do bloco "
        "da seção 4. Isso pode fazer o item 4 sumir da interface."
    )
