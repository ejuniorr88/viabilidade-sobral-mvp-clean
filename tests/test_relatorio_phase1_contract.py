from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase1_relatorio_keeps_new_structure_anchors() -> None:
    txt = (ROOT / "ui" / "relatorio.py").read_text(encoding="utf-8")

    for anchor in [
        "RELATÓRIO URBANÍSTICO",
        "Onde está localizado o terreno?",
        "O uso residencial unifamiliar é viável neste terreno?",
        "O que essa zona permite neste terreno?",
        "Resumo rápido final",
        "Fechamento final",
    ]:
        assert anchor in txt, f"ui/relatorio.py não contém o bloco textual esperado: {anchor}"


def test_phase1_relatorio_keeps_leiga_unifamiliar_sections() -> None:
    txt = (ROOT / "ui" / "relatorio.py").read_text(encoding="utf-8")

    expected = [
        "O que essa zona permite neste terreno?",
        "Quanto posso ocupar no térreo?",
        "Quanto preciso deixar livre?",
        "Posso construir mais andares?",
        "Preciso de vagas de estacionamento?",
        "O que preciso saber sobre a calçada?",
        "Dicas valiosas",
        "Resumo rápido final",
    ]

    for snippet in expected:
        assert snippet in txt, f"ui/relatorio.py não contém o bloco textual esperado: {snippet}"
