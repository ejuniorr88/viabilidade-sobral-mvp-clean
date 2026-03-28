from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _contains_any(text: str, variants: list[str]) -> bool:
    return any(v in text for v in variants)


def test_relatorio_smoke_must_keep_core_blocks() -> None:
    """
    Smoke test antirregressão:
    - falha se sumirem blocos/textos centrais do relatório
    - tolera pequenas variações de redação/título sem quebrar à toa
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
    txt_multi_common = (ROOT / "ui" / "relatorio_blocks" / "multifamiliar_items" / "common.py").read_text(encoding="utf-8")

    for anchor in [
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
    ]:
        assert anchor in txt_relatorio, f"Âncora obrigatória sumiu de ui/relatorio.py: {anchor}"

    quadro_variants = [
        "QUADRO TÉCNICO - PARÂMETROS DOS AMBIENTES",
        "QUADRO TÉCNICO – PARÂMETROS DOS AMBIENTES",
        "Quadro técnico — parâmetros dos ambientes",
        "Quadro técnico – parâmetros dos ambientes",
        "Quadro técnico - parâmetros dos ambientes",
        "PARÂMETROS DOS AMBIENTES",
    ]
    assert _contains_any(txt_quadro, quadro_variants), (
        "Âncora obrigatória sumiu de ui/relatorio_blocks/quadro_tecnico.py: "
        "título do quadro técnico."
    )

    for anchor in ["Observações", "Observações gerais"]:
        assert anchor in txt_quadro, f"Âncora obrigatória sumiu de ui/relatorio_blocks/quadro_tecnico.py: {anchor}"

    assert (
        "A largura mínima do degrau será de 0,25m." in txt_quadro
        or "Largura mínima do degrau: 0,25m." in txt_quadro
    ), "Âncora obrigatória sumiu de ui/relatorio_blocks/quadro_tecnico.py: largura mínima do degrau."

    assert (
        "A altura máxima do degrau será de 0,19m." in txt_quadro
        or "Altura máxima do degrau: 0,19m." in txt_quadro
    ), "Âncora obrigatória sumiu de ui/relatorio_blocks/quadro_tecnico.py: altura máxima do degrau."

    assert (
        "Dicas Valiosas" in txt_dicas or "Dicas valiosas" in txt_dicas
    ), "Âncora obrigatória sumiu de ui/relatorio_blocks/dicas_valiosas.py: Dicas Valiosas"

    for anchor in ["Abrir em tamanho real", "Anexo V"]:
        assert anchor in txt_figuras, f"Âncora obrigatória sumiu de ui/relatorio_blocks/figuras_anexo_v.py: {anchor}"

    assert "Vagas de estacionamento" in txt_multi, (
        "Âncora obrigatória sumiu de ui/relatorio_blocks/multifamiliar_guia.py: Vagas de estacionamento"
    )
    assert "quadra máxima" in txt_multi or "quadra máxima" in txt_multi_common, (
        "Âncora obrigatória sumiu do fluxo multifamiliar: quadra máxima"
    )
