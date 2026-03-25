from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding='utf-8')


def test_unifamiliar_has_specific_adequabilidade_helper() -> None:
    txt = _read('ui/relatorio.py')
    assert 'def _summarize_adequabilidade_unifamiliar' in txt
    assert 'A zona indicou I (Inadequado / não permitido).' in txt
    assert 'a via não libera um uso residencial que a zona já proibiu' in txt


def test_unifamiliar_relatorio_no_longer_is_hardcoded_as_viavel() -> None:
    txt = _read('ui/relatorio.py')
    assert 'status_curto == "PERMITE"' in txt
    assert 'status_curto == "NÃO PERMITE"' in txt
    assert 'zone_class, via_class, dbg = _fetch_adequabilidade(' in txt
