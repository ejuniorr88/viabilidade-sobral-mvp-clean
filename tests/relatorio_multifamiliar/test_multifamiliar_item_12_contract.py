from .test_multifamiliar_items_helpers import (
    assert_item_has_required_phrases,
    assert_main_heading_centralized,
    assert_guia_does_not_keep_residual_text,
)


def test_item_12_heading_principal_fica_somente_no_relatorio() -> None:
    assert_main_heading_centralized("item_12")


def test_item_12_keeps_minimum_content_contract() -> None:
    assert_item_has_required_phrases(
        "item_12",
        ['A análise do terreno não termina dentro do lote', 'render_figuras_anexo_v', 'rebaixo de meio-fio'],
    )


def test_item_12_content_does_not_fall_back_to_multifamiliar_guia() -> None:
    assert_guia_does_not_keep_residual_text(['render_figuras_anexo_v'])
