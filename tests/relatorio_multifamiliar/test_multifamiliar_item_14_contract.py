from .test_multifamiliar_items_helpers import (
    assert_item_has_required_phrases,
    assert_main_heading_centralized,
    assert_guia_does_not_keep_residual_text,
)


def test_item_14_heading_principal_fica_somente_no_relatorio() -> None:
    assert_main_heading_centralized("item_14")


def test_item_14_keeps_minimum_content_contract() -> None:
    assert_item_has_required_phrases(
        "item_14",
        ['Se você quiser ver só o essencial deste terreno', 'Área adotada no relatório', 'TO efetiva considerada', 'Área livre remanescente'],
    )


def test_item_14_content_does_not_fall_back_to_multifamiliar_guia() -> None:
    assert_guia_does_not_keep_residual_text(['Área adotada no relatório'])
