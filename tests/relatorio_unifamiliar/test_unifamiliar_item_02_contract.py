from .test_unifamiliar_items_helpers import (
    assert_item_has_required_phrases,
    assert_main_heading_centralized,
    assert_relatorio_does_not_keep_residual_text,
)


def test_item_02_heading_principal_fica_somente_no_relatorio() -> None:
    assert_main_heading_centralized("item_02")


def test_item_02_keeps_minimum_content_contract() -> None:
    assert_item_has_required_phrases(
        "item_02",
        [
            "Resumo final:",
        "Mesmo quando o resultado for positivo",
        "Ainda não foi possível encontrar a adequabilidade no banco"
        ],
    )


def test_item_02_content_does_not_fall_back_to_ui_relatorio() -> None:
    assert_relatorio_does_not_keep_residual_text(['Para o uso residencial unifamiliar, a permissão pode depender principalmente da zona'])
