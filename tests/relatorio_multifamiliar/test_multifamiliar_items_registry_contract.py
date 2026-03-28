from .test_multifamiliar_items_helpers import ITEM_FILES, ITEM_HEADINGS, ITEMS_DIR, read_guia, read_item


def test_multifamiliar_items_folder_has_all_16_item_files() -> None:
    for item_key, filename in ITEM_FILES.items():
        assert (ITEMS_DIR / filename).exists(), f"Arquivo do {item_key} não encontrado: {filename}"


def test_multifamiliar_registry_keeps_16_headings_in_order() -> None:
    txt = read_guia()
    positions = []
    for item_key in ITEM_HEADINGS:
        heading = ITEM_HEADINGS[item_key]
        assert txt.count(heading) == 1, f"Heading deve aparecer 1x: {heading}"
        positions.append(txt.find(heading))
    assert positions == sorted(positions), "A ordem dos headings do multifamiliar mudou no multifamiliar_guia.py."


def test_multifamiliar_items_use_single_render_entrypoint() -> None:
    for item_key, filename in ITEM_FILES.items():
        txt = read_item(item_key)
        assert txt.count('def render(') == 1, f"{filename} deve ter exatamente um render(...)."
