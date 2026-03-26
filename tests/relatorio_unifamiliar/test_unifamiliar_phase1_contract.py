from .test_unifamiliar_items_helpers import ITEM_HEADINGS, read_relatorio


def test_ui_relatorio_keeps_all_unifamiliar_main_headings() -> None:
    txt = read_relatorio()
    for heading in ITEM_HEADINGS.values():
        assert heading in txt, f"ui/relatorio.py perdeu heading obrigatório do unifamiliar: {heading}"


def test_ui_relatorio_uses_modular_unifamiliar_registry() -> None:
    txt = read_relatorio()
    assert 'from .relatorio_blocks.unifamiliar_items import UNIFAMILIAR_ITEM_RENDERERS' in txt
    assert 'for item_key in [' in txt
    assert 'UNIFAMILIAR_ITEM_RENDERERS[item_key](ctx)' in txt
