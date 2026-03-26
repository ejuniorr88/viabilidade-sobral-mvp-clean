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


def test_unifamiliar_json_block_stays_after_fechamento_header_only() -> None:
    txt = read_relatorio()
    fechamento = ITEM_HEADINGS['item_16']
    idx = txt.find(fechamento)
    assert idx != -1, "Fechamento final não encontrado."

    after = txt[idx:]
    assert 'with st.expander("Ver regra completa (JSON)")' in after, (
        "O expander de JSON pode existir no fluxo do unifamiliar, mas o fechamento final precisa continuar presente."
    )
