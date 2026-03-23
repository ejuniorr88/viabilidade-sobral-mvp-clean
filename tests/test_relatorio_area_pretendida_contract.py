from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_relatorio_unifamiliar_prioritizes_area_pretendida_in_text() -> None:
    txt = _read("ui/relatorio.py")
    required = [
        "área construída pretendida no térreo",
        "TO efetiva",
        "Área livre remanescente",
        "restam aproximadamente",
        "potencial construtivo para crescer acima",
    ]
    for item in required:
        assert item in txt, f"ui/relatorio.py perdeu a leitura contratual da área pretendida: {item}"



def test_relatorio_unifamiliar_keeps_maximum_reference_and_tp_reading() -> None:
    txt = _read("ui/relatorio.py")
    required = [
        "Esse é o limite máximo permitido pela **Taxa de Ocupação (TO)**.",
        "área permeável",
        "preservar a faixa permeável necessária",
        "Índice de Aproveitamento (IA)",
    ]
    for item in required:
        assert item in txt, f"ui/relatorio.py perdeu referência importante do bloco 5/6/8: {item}"



def test_relatorio_unifamiliar_passes_corner_flag_to_figuras() -> None:
    txt = _read("ui/relatorio.py")
    assert "render_figuras_anexo_v(rule, is_corner=is_corner)" in txt, (
        "ui/relatorio.py precisa repassar is_corner para as figuras do Anexo V."
    )
