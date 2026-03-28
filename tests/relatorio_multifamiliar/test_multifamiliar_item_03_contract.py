from .test_multifamiliar_items_helpers import (
    assert_item_has_required_phrases,
    assert_main_heading_centralized,
    assert_guia_does_not_keep_residual_text,
)


def test_item_03_heading_principal_fica_somente_no_relatorio() -> None:
    assert_main_heading_centralized("item_03")


def test_item_03_keeps_minimum_content_contract() -> None:
    assert_item_has_required_phrases(
        "item_03",
        ['| **A** | Adequado / permitido |', '| **Projeto especial** | acima de **5.000 m²** |', 'estas siglas ajudam a interpretar corretamente'],
    )


def test_item_03_content_does_not_fall_back_to_multifamiliar_guia() -> None:
    assert_guia_does_not_keep_residual_text(['| **AP/AM** | Depende do porte |'])
