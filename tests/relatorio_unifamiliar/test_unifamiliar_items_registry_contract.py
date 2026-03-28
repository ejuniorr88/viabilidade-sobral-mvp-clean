from .test_unifamiliar_items_helpers import (
    ITEM_FILES,
    ITEM_HEADINGS,
    ITEMS_DIR,
    expected_heading_count_in_relatorio,
    read_item,
    read_relatorio,
)


def test_unifamiliar_items_folder_has_all_16_item_files() -> None:
    for item_key, filename in ITEM_FILES.items():
        assert (ITEMS_DIR / filename).exists(), f"Arquivo do {item_key} não encontrado: {filename}"


def test_unifamiliar_registry_keeps_16_headings_in_order() -> None:
    txt = read_relatorio()
    positions = []
    for item_key in ITEM_HEADINGS:
        heading = ITEM_HEADINGS[item_key]
        expected_count = expected_heading_count_in_relatorio(item_key)
        assert txt.count(heading) == expected_count, f"Heading deve aparecer {expected_count}x: {heading}"
        positions.append(txt.find(heading))
    assert positions == sorted(positions), "A ordem dos headings do unifamiliar mudou no ui/relatorio.py."


def test_unifamiliar_items_use_render_entrypoint_only_once() -> None:
    for item_key, filename in ITEM_FILES.items():
        txt = read_item(item_key)
        assert txt.count('def render(ctx: dict) -> None:') == 1, f"{filename} deve ter exatamente um render(ctx)."
