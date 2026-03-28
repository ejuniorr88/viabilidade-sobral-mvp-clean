from .test_multifamiliar_items_helpers import ITEM_HEADINGS, assert_common_has_required_phrases, read_guia, read_item


def test_multifamiliar_keeps_zone_block_and_summary_phrase() -> None:
    guia_txt = read_guia()
    resumo_txt = read_item('item_14')

    assert ITEM_HEADINGS['item_04'] in guia_txt
    assert ITEM_HEADINGS['item_14'] in guia_txt
    assert 'Se você quiser ver só o essencial deste terreno' in resumo_txt
    assert 'Área adotada no relatório' in resumo_txt
    assert 'Área livre remanescente' in resumo_txt


def test_multifamiliar_alvara_block_exists_once_and_before_fechamento() -> None:
    guia_txt = read_guia()

    alvara = ITEM_HEADINGS['item_15']
    fechamento = ITEM_HEADINGS['item_16']

    assert guia_txt.count(alvara) == 1, 'Bloco do alvará do multifamiliar não pode se repetir.'
    idx_alvara = guia_txt.find(alvara)
    idx_fech = guia_txt.find(fechamento)

    assert idx_alvara != -1, 'Bloco do alvará não encontrado no multifamiliar.'
    assert idx_fech != -1, 'Fechamento final não encontrado no multifamiliar.'
    assert idx_alvara < idx_fech, 'O bloco do alvará precisa ficar antes do Fechamento final.'


def test_multifamiliar_alvara_has_two_paths_and_main_checklists() -> None:
    assert_common_has_required_phrases(
        [
            '#### 📄 Alvará de Construção Simplificado',
            '#### 🏗️ Alvará de Construção (Obra Nova)',
            'Documento de identidade do requerente ou representante legal',
            'Parecer favorável de Adequabilidade Locacional',
            'ART/RRT do responsável técnico',
            'Requerimento único',
            'Memorial de cálculo e drenagem pluvial',
            'EIV, quando exigido pela legislação',
            'st.markdown(f"- [ ] {item}")',
        ]
    )
