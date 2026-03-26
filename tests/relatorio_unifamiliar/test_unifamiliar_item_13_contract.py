from .test_unifamiliar_items_helpers import (
    assert_item_has_required_phrases,
    assert_main_heading_centralized,
    assert_relatorio_does_not_keep_residual_text,
)


def test_item_13_heading_principal_fica_somente_no_relatorio() -> None:
    assert_main_heading_centralized("item_13")


def test_item_13_keeps_minimum_content_contract() -> None:
    assert_item_has_required_phrases(
        "item_13",
        [
            "Flexibilidade de recuos no uso residencial unifamiliar",
        "Piscina não entra como área construída",
        "Não existe uma largura única e fixa para toda calçada no município"
        ],
    )


def test_item_13_content_does_not_fall_back_to_ui_relatorio() -> None:
    assert_relatorio_does_not_keep_residual_text(['Piscina não entra como área construída'])
