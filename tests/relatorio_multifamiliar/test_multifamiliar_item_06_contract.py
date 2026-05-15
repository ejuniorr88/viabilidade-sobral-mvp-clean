from .test_multifamiliar_items_helpers import (
    assert_item_has_required_phrases,
    assert_main_heading_centralized,
    assert_guia_does_not_keep_residual_text,
)


def test_item_06_heading_principal_fica_somente_no_relatorio() -> None:
    assert_main_heading_centralized("item_06")


def test_item_06_keeps_minimum_content_contract() -> None:
    assert_item_has_required_phrases(
        "item_06",
        ['A zona permite ocupar até', 'Texto didático para R2.1', 'Cenário A — unidades sobrepostas', 'Cenário B — unidades lado a lado', 'Área pretendida informada'],
    )


def test_item_06_content_does_not_fall_back_to_multifamiliar_guia() -> None:
    assert_guia_does_not_keep_residual_text(['Opção 2 — no caso do multifamiliar justaposto'])
