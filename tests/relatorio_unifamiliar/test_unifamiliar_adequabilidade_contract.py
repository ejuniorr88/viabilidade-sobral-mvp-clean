from .test_unifamiliar_items_helpers import read_item, read_relatorio


def test_unifamiliar_has_specific_adequabilidade_helper() -> None:
    txt = read_relatorio()
    assert 'def _fetch_adequabilidade_unifamiliar' in txt
    assert '_mf_fetch_adequabilidade(' in txt
    assert '_mf_summarize_adequabilidade(' in txt


def test_unifamiliar_relatorio_no_longer_is_hardcoded_as_viavel() -> None:
    txt = read_item('item_02')
    assert "ctx['status_curto'] == \"PERMITE\"" in txt
    assert "elif ctx['status_curto'] in" in txt
    assert 'st.error' in txt
