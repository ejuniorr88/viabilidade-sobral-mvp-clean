from .test_multifamiliar_items_helpers import (
    assert_item_has_required_phrases,
    assert_main_heading_centralized,
    assert_guia_does_not_keep_residual_text,
)


def test_item_04_heading_principal_fica_somente_no_relatorio() -> None:
    assert_main_heading_centralized("item_04")


def test_item_04_keeps_minimum_content_contract() -> None:
    assert_item_has_required_phrases(
        "item_04",
        ['Todo terreno está inserido em uma zona', 'Nas áreas urbanas, essas informações normalmente ajudam a definir', 'É essa leitura da zona que ajuda a entender o que pode ser implantado no lote'],
    )


def test_item_04_content_does_not_fall_back_to_multifamiliar_guia() -> None:
    assert_guia_does_not_keep_residual_text(['Todo terreno está inserido em uma zona'])
