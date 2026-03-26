from .test_unifamiliar_items_helpers import (
    assert_item_has_required_phrases,
    assert_main_heading_centralized,
    assert_relatorio_does_not_keep_residual_text,
)


def test_item_04_heading_principal_fica_somente_no_relatorio() -> None:
    assert_main_heading_centralized("item_04")


def test_item_04_keeps_minimum_content_contract() -> None:
    assert_item_has_required_phrases(
        "item_04",
        [
            "Todo terreno está inserido em uma zona, e cada zona pode ter regras, restrições e critérios próprios de uso e ocupação.",
            "Nas áreas urbanas, essas informações normalmente ajudam a definir o que pode ser construído",
            "Código de Ordenamento Urbano",
            "description_text",
            "É essa leitura da zona que ajuda a entender o que pode ser implantado no lote",
        ],
    )


def test_item_04_content_does_not_fall_back_to_ui_relatorio() -> None:
    assert_relatorio_does_not_keep_residual_text([
        'Todo terreno está inserido em uma zona, e cada zona pode ter regras, restrições e critérios próprios de uso e ocupação.',
        'Código de Ordenamento Urbano',
        'É essa leitura da zona que ajuda a entender o que pode ser implantado no lote',
    ])
