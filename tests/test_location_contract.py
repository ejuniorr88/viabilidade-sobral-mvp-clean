from core.zones_map import _normalize_zone


def test_location_contract_zeip_sector():
    props = {"sigla": "ZEIP", "subzona": "ZEIP 7", "zona_sigla": "ZEIP 7"}
    norm = _normalize_zone(props)
    assert norm["zone_sigla"] == "ZEIP"
    assert norm["subzone_code"] == "ZEIP_7"
    assert norm["display_label"] == "ZEIP 7"


def test_location_contract_zpp():
    props = {"sigla": "ZPP", "subzona": "ZPP 3", "zona_sigla": "ZPP 3"}
    norm = _normalize_zone(props)
    assert norm["zone_sigla"] == "ZPP 3"
    assert norm["subzone_code"] == "PADRAO"
    assert norm["display_label"] == "ZPP 3"


def test_location_contract_zeia_app():
    props = {"sigla": "ZEIA", "subzona": "ZEIA", "zona_sigla": "ZEIA / APP"}
    norm = _normalize_zone(props)
    assert norm["zone_sigla"] == "ZEIA-APP"
    assert norm["subzone_code"] == "PADRAO"
    assert norm["display_label"] == "ZEIA-APP"
