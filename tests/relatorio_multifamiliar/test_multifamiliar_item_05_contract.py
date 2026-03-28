from .test_multifamiliar_items_helpers import (
    assert_item_has_required_phrases,
    assert_main_heading_centralized,
    assert_guia_does_not_keep_residual_text,
)


def test_item_05_heading_principal_fica_somente_no_relatorio() -> None:
    assert_main_heading_centralized("item_05")


def test_item_05_keeps_minimum_content_contract() -> None:
    assert_item_has_required_phrases(
        "item_05",
        ['Depois de entender se o uso é permitido', 'TO máxima:', 'Esses são os parâmetros que mais influenciam o estudo inicial do projeto.'],
    )


def test_item_05_content_does_not_fall_back_to_multifamiliar_guia() -> None:
    assert_guia_does_not_keep_residual_text(['Esses são os parâmetros que mais influenciam o estudo inicial do projeto.'])
