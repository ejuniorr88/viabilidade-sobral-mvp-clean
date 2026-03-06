from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    p = ROOT / rel_path
    assert p.exists(), f"Arquivo não encontrado: {rel_path}"
    return p.read_text(encoding="utf-8", errors="ignore")


def test_relatorio_orquestrador_chama_blocos() -> None:
    txt = _read("ui/relatorio.py")
    assert "render_quadro_tecnico" in txt
    assert "render_dicas_valiosas" in txt
    assert "render_figuras_anexo_v" in txt


def test_bloco_quadro_tecnico_tem_textos_obrigatorios() -> None:
    txt = _read("ui/relatorio_blocks/quadro_tecnico.py")
    assert "QUADRO TÉCNICO – PARÂMETROS DOS AMBIENTES" in txt
    assert "Altura máxima do degrau: 0,19m." in txt


def test_bloco_dicas_valiosas_tem_titulo_obrigatorio() -> None:
    txt = _read("ui/relatorio_blocks/dicas_valiosas.py")
    assert "Dicas Valiosas" in txt


def test_bloco_figuras_anexo_v_tem_textos_obrigatorios() -> None:
    txt = _read("ui/relatorio_blocks/figuras_anexo_v.py")
    assert "Figuras anexas (Anexo V)" in txt
    assert "Abrir em tamanho real" in txt
