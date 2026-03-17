from core.zone_resolution import resolve_zone_context, build_lookup_candidates


def test_zpp_variants_resolve_same():
    a = resolve_zone_context(zone_sigla="ZPP", subzone="ZPP 1")
    b = resolve_zone_context(zone_sigla="ZPP 1", subzone="PADRAO")
    assert a.zone_sigla_db == "ZPP 1"
    assert b.zone_sigla_db == "ZPP 1"
    assert a.subzone_code_db == "PADRAO"
    assert b.subzone_code_db == "PADRAO"


def test_zeia_variants_preserved():
    a = resolve_zone_context(zone_sigla="ZEIA", subzone="ZEIA 2")
    b = resolve_zone_context(zone_sigla="ZEIA2", subzone="PADRAO")
    assert a.zone_sigla_db == "ZEIA2"
    assert b.zone_sigla_db == "ZEIA2"
    assert a.subzone_code_db == "PADRAO"
    assert b.subzone_code_db == "PADRAO"


def test_zeia_app_variants_preserved():
    a = resolve_zone_context(zone_sigla="ZEIA", subzone="ZEIA", zone_label="ZEIA / APP")
    b = resolve_zone_context(zone_sigla="ZEIA-APP", subzone="PADRAO")
    c = resolve_zone_context(zone_sigla="ZEIA/APP", subzone="PADRAO")
    assert a.zone_sigla_db == "ZEIA-APP"
    assert b.zone_sigla_db == "ZEIA-APP"
    assert c.zone_sigla_db == "ZEIA-APP"


def test_lookup_candidates_keep_zeia_and_zpp_paths():
    zpp = build_lookup_candidates("ZPP 3", "PADRAO")
    zeia = build_lookup_candidates("ZEIA 1", "PADRAO")
    assert ("ZPP 3", "PADRAO") in zpp or ("ZPP3", "PADRAO") in zpp
    assert ("ZEIA1", "PADRAO") in zeia or ("ZEIA 1", "PADRAO") in zeia
