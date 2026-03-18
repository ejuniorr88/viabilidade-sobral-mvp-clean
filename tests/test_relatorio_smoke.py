from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_relatorio_smoke_must_keep_core_blocks() -> None:
    """
    Smoke test antirregressão:

    Objetivo:
    - falhar se sumirem textos/blocos obrigatórios do relatório
    - reduzir chance de regressão ao mexer em ui/relatorio.py e ui/relatorio_blocks/*
    """

    relatorio_py = ROOT / "ui" / "relatorio.py"
    quadro_py = ROOT / "ui" / "relatorio_blocks" / "quadro_tecnico.py"
    dicas_py = ROOT / "ui" / "relatorio_blocks" / "dicas_valiosas.py"
    figuras_py = ROOT / "ui" / "relatorio_blocks" / "figuras_anexo_v.py"
    multi_py = ROOT / "ui" / "relatorio_blocks" / "multifamiliar_guia.py"

    assert relatorio_py.exists(), "ui/relatorio.py não encontrado"
    assert quadro_py.exists(), "ui/relatorio_blocks/quadro_tecnico.py não encontrado"
    assert dicas_py.exists(), "ui/relatorio_blocks/dicas_valiosas.py não encontrado"
    assert figuras_py.exists(), "ui/relatorio_blocks/figuras_anexo_v.py não encontrado"
    assert multi_py.exists(), "ui/relatorio_blocks/multifamiliar_guia.py não encontrado"

    txt_relatorio = relatorio_py.read_text(encoding="utf-8")
    txt_quadro = quadro_py.read_text(encoding="utf-8")
    txt_dicas = dicas_py.read_text(encoding="utf-8")
    txt_figuras = figuras_py.read_text(encoding="utf-8")
    txt_multi = multi_py.read_text(encoding="utf-8")

    core_anchors_by_file = {
        "ui/relatorio.py": [
            "RELATÓRIO URBANÍSTICO",
            "Onde está localizado o terreno?",
            "O uso residencial unifamiliar é viável neste terreno?",
            "O que essa zona permite neste terreno?",
            "Quanto posso ocupar no térreo?",
            "Quanto preciso deixar livre?",
            "Tipos de piso: o que conta como permeável?",
            "Preciso de vagas de estacionamento?",
            "Dicas valiosas",
            "Resumo rápido final",
        ],
        "ui/relatorio_blocks/quadro_tecnico.py": [
            "QUADRO TÉCNICO - PARÂMETROS DOS AMBIENTES",
            "Observações",
            "Observações gerais",
            # Âncoras atualizadas para o texto fiel ao Anexo
            "A largura mínima do degrau será de 0,25m.",
            "A altura máxima do degrau será de 0,19m.",
        ],
        "ui/relatorio_blocks/dicas_valiosas.py": [
            "Dicas Valiosas",
        ],
        "ui/relatorio_blocks/figuras_anexo_v.py": [
            "Abrir em tamanho real",
            "Anexo V",
        ],
        "ui/relatorio_blocks/multifamiliar_guia.py": [
            "Vagas de estacionamento",
            "quadro máxima",
        ],
    }

    texts = {
        "ui/relatorio.py": txt_relatorio,
        "ui/relatorio_blocks/quadro_tecnico.py": txt_quadro,
        "ui/relatorio_blocks/dicas_valiosas.py": txt_dicas,
        "ui/relatorio_blocks/figuras_anexo_v.py": txt_figuras,
        "ui/relatorio_blocks/multifamiliar_guia.py": txt_multi,
    }

    for filename, anchors in core_anchors_by_file.items():
        txt = texts[filename]
        for s in anchors:
            assert s in txt, f"Âncora obrigatória sumiu de {filename}: {s}"
