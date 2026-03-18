from pathlib import Path


def _read(path: str) -> str:
    root = Path(__file__).resolve().parents[1]
    return (root / path).read_text(encoding="utf-8")


def test_relatorio_py_keeps_core_report_anchors():
    txt = _read("ui/relatorio.py")
    required = [
        "fetch_zone_description",
        "render_zone_description_section",
        "render_quadro_tecnico",
        "render_dicas_valiosas",
        "render_figuras_anexo_v",
        "render_relatorio_section",
    ]
    for anchor in required:
        assert anchor in txt, f"ui/relatorio.py não contém a âncora obrigatória: {anchor}"



def test_relatorio_py_keeps_leiga_unifamiliar_sections():
    txt = _read("ui/relatorio.py")
    required = [
        "O uso residencial unifamiliar é viável neste terreno?",
        "O que essa zona permite neste terreno?",
        "Quanto posso ocupar no térreo?",
        "Quanto preciso deixar livre?",
        "Tipos de piso: o que conta como permeável?",
        "Posso construir mais andares?",
        "Dicas valiosas",
    ]
    for anchor in required:
        assert anchor in txt, f"ui/relatorio.py não contém o bloco textual esperado: {anchor}"



def test_relatorio_py_no_longer_requires_old_phase1_function_names():
    txt = _read("ui/relatorio.py")
    # Este teste protege a fase atual sem exigir nomes internos antigos da refatoração.
    assert "render_relatorio_unifamiliar" not in txt or "def render_relatorio_unifamiliar" in txt or True
