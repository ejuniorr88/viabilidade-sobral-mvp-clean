from tests.relatorio_multifamiliar.test_multifamiliar_items_helpers import ITEM_HEADINGS, assert_common_has_required_phrases, read_guia


def test_multifamiliar_final_anchors_are_unique_and_ordered() -> None:
    txt = read_guia()

    anchors = [
        ITEM_HEADINGS['item_11'],
        ITEM_HEADINGS['item_12'],
        ITEM_HEADINGS['item_13'],
        ITEM_HEADINGS['item_14'],
        ITEM_HEADINGS['item_15'],
        ITEM_HEADINGS['item_16'],
    ]

    positions = []
    for anchor in anchors:
        count = txt.count(anchor)
        assert count == 1, f"Âncora do multifamiliar deve aparecer 1x. Encontrado {count}x: {anchor}"
        positions.append(txt.find(anchor))

    assert positions == sorted(positions), "A ordem dos blocos finais do multifamiliar foi alterada."


def test_multifamiliar_alvara_content_kept() -> None:
    assert_common_has_required_phrases(
        [
            'Após a finalização dos projetos, será necessário dar entrada na documentação junto à **Prefeitura** para obter o **alvará de construção**.',
            '#### 📄 Alvará de Construção Simplificado',
            '#### 🏗️ Alvará de Construção (Obra Nova)',
            'Documento de identidade do requerente ou representante legal',
            'Parecer favorável de Adequabilidade Locacional',
            'ART/RRT do responsável técnico',
            'Requerimento único',
            'st.markdown(f"- [ ] {item}")',
        ]
    )
