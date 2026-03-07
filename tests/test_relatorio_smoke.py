from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_relatorio_smoke_must_keep_core_blocks() -> None:
    """
    Smoke test antirregressão:

    Objetivo:
    - falhar se sumirem textos/blocos obrigatórios do relatório
    - reduzir chance de regressão ao mexer em ui/relatorio.py e ui/relatorio_blocks/*
    """

    relatorio_py = ROOT / "ui" / "relatorio.py"
    assert relatorio_py.exists(), "ui/relatorio.py não encontrado"
    txt_rel = _read(relatorio_py)

    # 1) Âncoras do relatório (core)
    required_core = [
        "Altura máxima do degrau: 0,19m.",
        "Dicas Valiosas",
        "QUADRO TÉCNICO – PARÂMETROS DOS AMBIENTES",
        "Abrir em tamanho real",
        "Anexo V",
    ]
    for s in required_core:
        assert s in txt_rel, f"Âncora obrigatória sumiu de ui/relatorio.py: {s}"

    # 2) Orquestração deve chamar os blocos fixos (blindagem)
    required_calls = [
        "render_quadro_tecnico",
        "render_dicas_valiosas",
        "render_figuras_anexo_v",
    ]
    for s in required_calls:
        assert s in txt_rel, f"ui/relatorio.py não referencia o bloco: {s}"

    # 3) Âncoras do guia multifamiliar (Fase 1)
    multi_py = ROOT / "ui" / "relatorio_blocks" / "multifamiliar_guia.py"
    assert multi_py.exists(), "ui/relatorio_blocks/multifamiliar_guia.py não encontrado"
    txt_multi = _read(multi_py)

    required_multi = [
        "Multifamiliar — Fase 1 (Guia do Projetista)",
        "Como interpretar este resultado (bem simples):",
        "O que significam as siglas (bem simples):",
        "O que é “porte” (pequeno / médio / grande)?",
        "Via identificada como VIA LOCAL",
        "tabela por tipo de via",
    ]
    for s in required_multi:
        assert s in txt_multi, f"Âncora do multifamiliar sumiu: {s}"
