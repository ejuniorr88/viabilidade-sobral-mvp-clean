from .test_unifamiliar_items_helpers import ITEM_HEADINGS, read_item, read_relatorio


def test_unifamiliar_keeps_zone_block_and_summary_phrase() -> None:
    relatorio_txt = read_relatorio()
    resumo_txt = read_item('item_14')

    assert ITEM_HEADINGS['item_04'] in relatorio_txt
    assert ITEM_HEADINGS['item_14'] in relatorio_txt
    assert '👉 **Em resumo:**' in resumo_txt
    assert 'você pode ocupar até' in resumo_txt
    assert 'precisa manter pelo menos' in resumo_txt


def test_unifamiliar_alvara_block_exists_once_and_before_fechamento() -> None:
    relatorio_txt = read_relatorio()

    alvara = ITEM_HEADINGS['item_15']
    fechamento = ITEM_HEADINGS['item_16']

    assert relatorio_txt.count(alvara) == 1, 'Bloco do alvará do unifamiliar não pode se repetir.'
    idx_alvara = relatorio_txt.find(alvara)
    idx_fech = relatorio_txt.find(fechamento)

    assert idx_alvara != -1, 'Bloco do alvará não encontrado no unifamiliar.'
    assert idx_fech != -1, 'Fechamento final não encontrado no unifamiliar.'
    assert idx_alvara < idx_fech, 'O bloco do alvará precisa ficar antes do Fechamento final.'


def test_unifamiliar_alvara_has_two_paths_and_main_checklists() -> None:
    txt = read_item('item_15')

    required = [
        '#### 📄 Alvará de Construção Simplificado',
        '#### 🏗️ Alvará de Construção (Obra Nova)',
        '[ ] Documento de identidade do requerente ou representante legal',
        '[ ] CPF ou CNPJ',
        '[ ] Matrícula atualizada do imóvel ou documento equivalente',
        '[ ] Parecer favorável de Adequabilidade Locacional',
        '[ ] ART/RRT do responsável técnico',
        '[ ] Requerimento único',
        '[ ] Projeto hidrossanitário',
        '[ ] Memorial de cálculo e drenagem pluvial',
        '[ ] EIV, quando exigido pela legislação',
        '[ ] Conferir se o projeto atende às exigências técnicas antes do protocolo',
    ]
    for item in required:
        assert item in txt, f'Bloco do alvará/checklist do unifamiliar perdeu item obrigatório: {item}'


def test_unifamiliar_checklist_is_textual_not_disabled_checkbox() -> None:
    txt = read_item('item_15')
    assert 'st.checkbox(' not in txt, (
        'O checklist do alvará no unifamiliar deve ser textual ([ ] item), não checkbox desabilitado.'
    )
    assert '[ ] Documento de identidade do requerente ou representante legal' in txt
    assert '[ ] Requerimento único' in txt
