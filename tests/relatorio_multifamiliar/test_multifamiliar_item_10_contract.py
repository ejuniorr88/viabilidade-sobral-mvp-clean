from .test_multifamiliar_items_helpers import (
    assert_item_has_required_phrases,
    assert_main_heading_centralized,
    assert_guia_does_not_keep_residual_text,
)


def test_item_10_heading_principal_fica_somente_no_relatorio() -> None:
    assert_main_heading_centralized("item_10")


def test_item_10_keeps_minimum_content_contract() -> None:
    assert_item_has_required_phrases(
        "item_10",
        ['1 vaga por unidade', '1,5 vaga por unidade', 'redução de até 20% das vagas'],
    )


def test_item_10_content_does_not_fall_back_to_multifamiliar_guia() -> None:
    assert_guia_does_not_keep_residual_text(['redução de até 20% das vagas'])
