from .test_multifamiliar_items_helpers import (
    assert_item_has_required_phrases,
    assert_main_heading_centralized,
    assert_guia_does_not_keep_residual_text,
)


def test_item_16_heading_principal_fica_somente_no_relatorio() -> None:
    assert_main_heading_centralized("item_16")


def test_item_16_keeps_minimum_content_contract() -> None:
    assert_item_has_required_phrases(
        "item_16",
        ['Este relatório foi pensado para ajudar a entender o terreno de forma mais simples.', 'licenciamento de obras da prefeitura'],
    )


def test_item_16_content_does_not_fall_back_to_multifamiliar_guia() -> None:
    assert_guia_does_not_keep_residual_text(['Este relatório foi pensado para ajudar a entender o terreno de forma mais simples.'])
