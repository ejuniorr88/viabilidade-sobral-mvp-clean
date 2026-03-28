from .test_multifamiliar_items_helpers import (
    assert_item_has_required_phrases,
    assert_main_heading_centralized,
    assert_guia_does_not_keep_residual_text,
)


def test_item_15_heading_principal_fica_somente_no_relatorio() -> None:
    assert_main_heading_centralized("item_15")


def test_item_15_keeps_minimum_content_contract() -> None:
    assert_item_has_required_phrases(
        "item_15",
        ['_render_alvara_section'],
    )


def test_item_15_content_does_not_fall_back_to_multifamiliar_guia() -> None:
    assert_guia_does_not_keep_residual_text(['_render_alvara_section'])
