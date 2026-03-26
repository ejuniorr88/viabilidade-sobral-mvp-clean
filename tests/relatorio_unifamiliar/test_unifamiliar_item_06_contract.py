from .test_unifamiliar_items_helpers import (
    assert_item_has_required_phrases,
    assert_main_heading_centralized,
    assert_relatorio_does_not_keep_residual_text,
)


def test_item_06_heading_principal_fica_somente_no_relatorio() -> None:
    assert_main_heading_centralized("item_06")


def test_item_06_keeps_minimum_content_contract() -> None:
    assert_item_has_required_phrases(
        "item_06",
        [
            "Art. 112.",
        "Opção principal — aproveitando a flexibilidade da lei",
        "Opção alternativa — adotando os recuos da zona"
        ],
    )


def test_item_06_content_does_not_fall_back_to_ui_relatorio() -> None:
    assert_relatorio_does_not_keep_residual_text(['Art. 112.'])
