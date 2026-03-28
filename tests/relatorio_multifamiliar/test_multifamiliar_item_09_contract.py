from .test_multifamiliar_items_helpers import (
    assert_item_has_required_phrases,
    assert_main_heading_centralized,
    assert_guia_does_not_keep_residual_text,
)


def test_item_09_heading_principal_fica_somente_no_relatorio() -> None:
    assert_main_heading_centralized("item_09")


def test_item_09_keeps_minimum_content_contract() -> None:
    assert_item_has_required_phrases(
        "item_09",
        ['Índice de Aproveitamento (IA)', 'Altura máxima da zona:', 'Isso é apenas uma referência inicial'],
    )


def test_item_09_content_does_not_fall_back_to_multifamiliar_guia() -> None:
    assert_guia_does_not_keep_residual_text(['Isso é apenas uma referência inicial'])
