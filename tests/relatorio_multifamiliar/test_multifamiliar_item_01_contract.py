from .test_multifamiliar_items_helpers import (
    assert_item_has_required_phrases,
    assert_main_heading_centralized,
    assert_guia_does_not_keep_residual_text,
)


def test_item_01_heading_principal_fica_somente_no_relatorio() -> None:
    assert_main_heading_centralized("item_01")


def test_item_01_keeps_minimum_content_contract() -> None:
    assert_item_has_required_phrases(
        "item_01",
        ['Uso informado:', 'Área do terreno:', 'Essas informações são a base de toda a leitura do relatório.'],
    )


def test_item_01_content_does_not_fall_back_to_multifamiliar_guia() -> None:
    assert_guia_does_not_keep_residual_text(['Aqui entram:'])
