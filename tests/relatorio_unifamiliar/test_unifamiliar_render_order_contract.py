from .test_unifamiliar_items_helpers import ITEM_HEADINGS, read_relatorio


def test_unifamiliar_render_order_stable_at_end() -> None:
    txt = read_relatorio()

    anchors = [
        ITEM_HEADINGS['item_13'],
        ITEM_HEADINGS['item_14'],
        ITEM_HEADINGS['item_15'],
        ITEM_HEADINGS['item_16'],
    ]

    positions = []
    for anchor in anchors:
        count = txt.count(anchor)
        assert count == 1, f"Âncora final do unifamiliar deve aparecer 1x. Encontrado {count}x: {anchor}"
        idx = txt.find(anchor)
        positions.append(idx)

    assert positions == sorted(positions), "A ordem final dos blocos do unifamiliar foi alterada."


def test_unifamiliar_json_block_is_hidden_from_final_ui() -> None:
    txt = read_relatorio()
    fechamento = ITEM_HEADINGS['item_16']
    idx = txt.find(fechamento)
    assert idx != -1, "Fechamento final não encontrado."

    assert 'with st.expander("Ver regra completa (JSON)")' not in txt
    assert 'st.json(rule)' not in txt
