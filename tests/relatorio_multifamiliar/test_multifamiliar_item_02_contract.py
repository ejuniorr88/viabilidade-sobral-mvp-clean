from __future__ import annotations

import py_compile

from .test_multifamiliar_items_helpers import (
    assert_item_has_required_phrases,
    assert_main_heading_centralized,
    assert_guia_does_not_keep_residual_text,
    ITEMS_DIR,
)


ITEM_PATH = ITEMS_DIR / "item_02_adequabilidade.py"


def test_item_02_heading_principal_fica_somente_no_relatorio() -> None:
    assert_main_heading_centralized("item_02")


def test_item_02_compila_sem_erro_de_indentacao() -> None:
    py_compile.compile(str(ITEM_PATH), doraise=True)


def test_item_02_keeps_minimum_content_contract() -> None:
    assert_item_has_required_phrases(
        "item_02",
        [
            "Resumo final:",
            "Ainda não foi possível encontrar a adequabilidade no banco",
            "as regras de uso e ocupação do solo da zona",
            "classificação da via de acesso pelo sistema viário",
        ],
    )


def test_item_02_remove_frase_repetida_de_to_tp_ia() -> None:
    txt = ITEM_PATH.read_text(encoding="utf-8")
    assert "Mesmo quando o resultado for positivo" not in txt


def test_item_02_status_positivos_usam_card_verde() -> None:
    txt = ITEM_PATH.read_text(encoding="utf-8")

    assert 'common.st.success' in txt
    for status in (
        "PERMITE",
        "PERMITE SOMENTE PEQUENO PORTE",
        "PERMITE PEQUENO OU MÉDIO PORTE",
        "PERMITE PELA VIA",
        "PERMITE PELA VIA SOMENTE PEQUENO PORTE",
        "PERMITE PELA VIA PEQUENO OU MÉDIO PORTE",
    ):
        assert status in txt


def test_item_02_content_does_not_fall_back_to_multifamiliar_guia() -> None:
    assert_guia_does_not_keep_residual_text([
        "Para o uso residencial multifamiliar, a permissão pode depender principalmente da zona"
    ])
