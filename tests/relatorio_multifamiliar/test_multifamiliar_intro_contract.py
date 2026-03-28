from .test_multifamiliar_items_helpers import assert_intro_has_required_phrases


def test_intro_keeps_minimum_content_contract() -> None:
    assert_intro_has_required_phrases(
        [
            "## 🏢 RELATÓRIO URBANÍSTICO",
            "Este relatório mostra, de forma simples",
            "Importante:",
            "_render_intro_tipo",
        ]
    )
