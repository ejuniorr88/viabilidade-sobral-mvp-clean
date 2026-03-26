from .test_unifamiliar_items_helpers import (
    assert_item_has_required_phrases,
    assert_main_heading_centralized,
    assert_relatorio_does_not_keep_residual_text,
)


def test_item_15_heading_principal_fica_somente_no_relatorio() -> None:
    assert_main_heading_centralized("item_15")


def test_item_15_keeps_minimum_content_contract() -> None:
    assert_item_has_required_phrases(
        "item_15",
        [
            "#### 📄 Alvará de Construção Simplificado",
        "#### 🏗️ Alvará de Construção (Obra Nova)",
        "[ ] Aprovação do IPHAN, quando o imóvel estiver em ZEIP"
        ],
    )


def test_item_15_content_does_not_fall_back_to_ui_relatorio() -> None:
    assert_relatorio_does_not_keep_residual_text(['#### 📄 Alvará de Construção Simplificado',
        '[ ] Aprovação do IPHAN, quando o imóvel estiver em ZEIP'])
