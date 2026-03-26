from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_relatorio_unifamiliar_prioritizes_area_pretendida_in_text() -> None:
    required_by_file = {
        "ui/relatorio_blocks/unifamiliar_items/item_07_permeabilidade.py": [
            "área pretendida inicial",
            "área pretendida informada",
            "Área livre remanescente",
        ],
        "ui/relatorio_blocks/unifamiliar_items/item_09_ia_altura.py": [
            "potencial construtivo",
        ],
        "ui/relatorio_blocks/unifamiliar_items/item_14_resumo.py": [
            "TO considerada",
            "área livre remanescente",
        ],
    }
    for rel_path, required in required_by_file.items():
        txt = _read(rel_path)
        for item in required:
            assert item in txt, f"{rel_path} perdeu a leitura contratual da área pretendida: {item}"


def test_relatorio_unifamiliar_keeps_maximum_reference_and_tp_reading() -> None:
    required_by_file = {
        "ui/relatorio_blocks/unifamiliar_items/item_06_ocupacao_terreo.py": [
            "Esse é o limite máximo permitido pela **Taxa de Ocupação (TO)**.",
        ],
        "ui/relatorio_blocks/unifamiliar_items/item_07_permeabilidade.py": [
            "área permeável",
            "devem permanecer permeáveis",
        ],
        "ui/relatorio_blocks/unifamiliar_items/item_09_ia_altura.py": [
            "Índice de Aproveitamento (IA)",
        ],
    }
    for rel_path, required in required_by_file.items():
        txt = _read(rel_path)
        for item in required:
            assert item in txt, f"{rel_path} perdeu referência importante do bloco 5/6/8: {item}"


def test_relatorio_unifamiliar_passes_corner_flag_to_figuras() -> None:
    txt = _read("ui/relatorio_blocks/unifamiliar_items/item_12_calcada.py")
    assert "ctx['render_figuras_anexo_v'](ctx['rule'], is_corner=ctx['is_corner'])" in txt, (
        "item_12_calcada.py precisa repassar is_corner para as figuras do Anexo V."
    )
