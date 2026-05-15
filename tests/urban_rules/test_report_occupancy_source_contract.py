from pathlib import Path


def test_multifamiliar_item06_usa_regra_comum_to_recuos():
    source = Path('ui/relatorio_blocks/multifamiliar_items/item_06_ocupacao_terreo.py').read_text(encoding='utf-8')

    assert 'choose_regular_occupancy' in source
    assert 'os recuos são mais restritivos que a TO' in source
    assert 'menor limite aplicável entre área pretendida, TO e recuos' in source


def test_multifamiliar_item07_permeabilidade_usa_mesma_area_adotada():
    source = Path('ui/relatorio_blocks/multifamiliar_items/item_07_permeabilidade.py').read_text(encoding='utf-8')

    assert 'choose_regular_occupancy' in source
    assert 'mesma área adotada no item de ocupação do térreo' in source
    assert 'base_ocupacao = decision.area_adotada' in source
