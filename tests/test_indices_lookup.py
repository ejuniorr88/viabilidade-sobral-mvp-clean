from unittest.mock import patch

from core.supabase_rules import fetch_rule


class _Resp:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, table_name, store):
        self.table_name = table_name
        self.store = store
        self.filters = {}

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, key, value):
        self.filters[key] = value
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        rows = self.store.get(self.table_name, [])
        out = []
        for row in rows:
            ok = True
            for k, v in self.filters.items():
                if row.get(k) != v:
                    ok = False
                    break
            if ok:
                out.append(row)
        return _Resp(out[:1])


class _SB:
    def __init__(self, store):
        self.store = store

    def table(self, name):
        return _Query(name, self.store)


def _sample_store():
    return {
        "zone_rules": [
            {"zone_sigla": "ZPP 1", "subzone_code": "PADRAO", "use_type_code": "RES_UNI", "to_max_pct": 70, "tp_min_pct": 20},
            {"zone_sigla": "ZPP 2", "subzone_code": "PADRAO", "use_type_code": "RES_UNI", "to_max_pct": 60, "tp_min_pct": 30},
            {"zone_sigla": "ZPP 3", "subzone_code": "PADRAO", "use_type_code": "RES_UNI", "to_max_pct": 60, "tp_min_pct": 30},
            {"zone_sigla": "ZEIA-APP", "subzone_code": "PADRAO", "use_type_code": "RES_UNI", "to_max_pct": 0, "tp_min_pct": 100},
            {"zone_sigla": "ZEIA1", "subzone_code": "PADRAO", "use_type_code": "RES_UNI", "to_max_pct": 15, "tp_min_pct": 80},
            {"zone_sigla": "ZEIA2", "subzone_code": "PADRAO", "use_type_code": "RES_UNI", "to_max_pct": 25, "tp_min_pct": 70},
            {"zone_sigla": "ZEIA3", "subzone_code": "PADRAO", "use_type_code": "RES_UNI", "to_max_pct": 15, "tp_min_pct": 80},
        ]
    }


@patch("core.supabase_rules.get_supabase")
def test_fetch_rule_zpp_variants(mock_get_supabase):
    fetch_rule.cache_clear()
    mock_get_supabase.return_value = _SB(_sample_store())
    rule = fetch_rule("ZPP 1", "RES_UNI", "PADRAO")
    assert rule is not None
    assert rule["to_max_pct"] == 70


@patch("core.supabase_rules.get_supabase")
def test_fetch_rule_zeia_variants(mock_get_supabase):
    fetch_rule.cache_clear()
    mock_get_supabase.return_value = _SB(_sample_store())
    rule = fetch_rule("ZEIA 2", "RES_UNI", "PADRAO")
    assert rule is not None
    assert rule["to_max_pct"] == 25


@patch("core.supabase_rules.get_supabase")
def test_fetch_rule_zeia_app_variants(mock_get_supabase):
    fetch_rule.cache_clear()
    mock_get_supabase.return_value = _SB(_sample_store())
    rule = fetch_rule("ZEIA/APP", "RES_UNI", "PADRAO")
    assert rule is not None
    assert rule["tp_min_pct"] == 100
