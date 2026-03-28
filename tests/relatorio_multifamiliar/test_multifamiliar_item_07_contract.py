from .test_multifamiliar_items_helpers import (
    assert_item_has_required_phrases,
    assert_main_heading_centralized,
    assert_guia_does_not_keep_residual_text,
)


def test_item_07_heading_principal_fica_somente_no_relatorio() -> None:
    assert_main_heading_centralized("item_07")


def test_item_07_keeps_minimum_content_contract() -> None:
    assert_item_has_required_phrases(
        "item_07",
        ['A zona exige', 'Cenário 1 — usando o máximo da TO', 'Cenário 2 — usando a implantação pelos recuos da zona', 'Leitura prática:'],
    )


def test_item_07_content_does_not_fall_back_to_multifamiliar_guia() -> None:
    assert_guia_does_not_keep_residual_text(['Cenário 1 — usando o máximo da TO'])
