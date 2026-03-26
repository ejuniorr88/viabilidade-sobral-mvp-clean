from .test_unifamiliar_items_helpers import (
    assert_item_has_required_phrases,
    assert_main_heading_centralized,
    assert_relatorio_does_not_keep_residual_text,
)


def test_item_07_heading_principal_fica_somente_no_relatorio() -> None:
    assert_main_heading_centralized("item_07")


def test_item_07_keeps_minimum_content_contract() -> None:
    assert_item_has_required_phrases(
        "item_07",
        [
            "A zona exige",
        "Área livre remanescente no lote",
        "Leitura prática:"
        ],
    )


def test_item_07_content_does_not_fall_back_to_ui_relatorio() -> None:
    assert_relatorio_does_not_keep_residual_text(['Área livre remanescente no lote'])



def test_item_07_cenario_order_contract() -> None:
    from pathlib import Path

    item_text = Path("ui/relatorio_blocks/unifamiliar_items/item_07_permeabilidade.py").read_text()
    idx_op2 = item_text.index("Cenário pela Opção 2 (Art. 112)")
    idx_op1 = item_text.index("Cenário pela Opção 1 (recuos padrão)")
    assert idx_op2 < idx_op1, "Item 7 deve mostrar primeiro a Opção 2 e depois a Opção 1."
