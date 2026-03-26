from .test_unifamiliar_items_helpers import (
    assert_item_has_required_phrases,
    assert_main_heading_centralized,
    assert_relatorio_does_not_keep_residual_text,
)


def test_item_05_heading_principal_fica_somente_no_relatorio() -> None:
    assert_main_heading_centralized("item_05")


def test_item_05_keeps_minimum_content_contract() -> None:
    assert_item_has_required_phrases(
        "item_05",
        [
            "Resumo das regras",
        "TO máxima:",
        "Essas são as regras que mais impactam o projeto."
        ],
    )


def test_item_05_content_does_not_fall_back_to_ui_relatorio() -> None:
    assert_relatorio_does_not_keep_residual_text(['Essas são as regras que mais impactam o projeto.'])
