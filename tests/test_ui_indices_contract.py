from contextlib import contextmanager
import sys
import types


streamlit_stub = types.SimpleNamespace(
    header=lambda *args, **kwargs: None,
    info=lambda *args, **kwargs: None,
    metric=lambda *args, **kwargs: None,
    columns=lambda n: [None] * n,
    expander=lambda *args, **kwargs: contextmanager(lambda: (yield))(),
    json=lambda *args, **kwargs: None,
)
sys.modules.setdefault("streamlit", streamlit_stub)

import ui.indices as indices_mod


class _DummyColumn:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@contextmanager
def _dummy_expander(*_args, **_kwargs):
    yield None


class _FakeStreamlit:
    def __init__(self):
        self.headers = []
        self.infos = []
        self.metrics = []
        self.json_payloads = []

    def header(self, text):
        self.headers.append(text)

    def info(self, text):
        self.infos.append(text)

    def metric(self, title, value):
        self.metrics.append((title, value))

    def columns(self, n):
        return [_DummyColumn() for _ in range(n)]

    def expander(self, *_args, **_kwargs):
        return _dummy_expander()

    def json(self, payload):
        self.json_payloads.append(payload)


def _patch_streamlit(monkeypatch):
    fake = _FakeStreamlit()
    monkeypatch.setattr(indices_mod, "st", fake)
    return fake


def _capture_cards():
    cards = []

    def card_func(title, value):
        cards.append((title, value))

    return cards, card_func


def _find_value(cards, title):
    for card_title, value in cards:
        if card_title == title:
            return value
    raise AssertionError(f"Card '{title}' não encontrado. Cards: {cards}")


def _base_calc(rule=None, **extra):
    payload = {
        "zone_lookup": "ZAP",
        "use_type_code": "RES_UNI",
        "rule": rule
        or {
            "zone_sigla": "ZAP",
            "subzone_code": "PADRAO",
            "tp_min": 0.25,
            "to_max": 0.65,
            "ia_max": 2.5,
            "ia_min": 0.2,
            "recuo_frontal_m": 3,
            "recuo_lateral_m": 1.5,
            "recuo_fundos_m": 1.5,
            "area_min_lote_m2": 125,
            "area_max_lote_m2": 62500,
            "testada_min_meio_m": 5,
            "testada_min_esquina_m": 7,
            "testada_max_m": 250,
            "gabarito_m": 48,
        },
    }
    payload.update(extra)
    return payload


def test_render_indices_section_shows_info_when_zone_or_use_type_missing(monkeypatch):
    fake = _patch_streamlit(monkeypatch)

    indices_mod.render_indices_section(calc={})

    assert fake.infos == [
        "Clique em Gerar consulta aos índices urbanísticos para carregar zona, via e índices urbanísticos."
    ]


def test_render_indices_section_zepe1_shows_textual_recuo_lateral(monkeypatch):
    _patch_streamlit(monkeypatch)
    cards, card_func = _capture_cards()
    calc = _base_calc(
        rule={
            "zone_sigla": "ZEPE1",
            "subzone_code": "PADRAO",
            "tp_min": 0.30,
            "to_max": 0.60,
            "ia_max": 1.0,
            "recuo_frontal_m": 5,
            "recuo_lateral_m": 1.5,
            "recuo_fundos_m": 3,
            "area_min_lote_m2": 250,
            "area_max_lote_m2": 40000,
            "testada_min_meio_m": 10,
            "testada_max_m": 500,
            "gabarito_m": 25,
        },
        zone_lookup="ZEPE1",
    )

    indices_mod.render_indices_section(calc=calc, card_func=card_func)

    assert _find_value(cards, "Recuo Lateral") == "3m - Uso Industrial / 1,5m - Outros Usos"


def test_render_indices_section_zepe2_shows_textual_recuo_lateral(monkeypatch):
    _patch_streamlit(monkeypatch)
    cards, card_func = _capture_cards()
    calc = _base_calc(
        rule={
            "zone_sigla": "ZEPE2",
            "subzone_code": "PADRAO",
            "tp_min": 0.30,
            "to_max": 0.60,
            "ia_max": 1.5,
            "recuo_frontal_m": 5,
            "recuo_lateral_m": 1.5,
            "recuo_fundos_m": 3,
            "area_min_lote_m2": 250,
            "area_max_lote_m2": 40000,
            "testada_min_meio_m": 10,
            "testada_max_m": 500,
            "gabarito_m": 25,
        },
        zone_lookup="ZEPE2",
    )

    indices_mod.render_indices_section(calc=calc, card_func=card_func)

    assert _find_value(cards, "Recuo Lateral") == "3m - Uso Industrial / 1,5m - Outros Usos"


def test_render_indices_section_non_zepe_keeps_numeric_recuo_lateral(monkeypatch):
    _patch_streamlit(monkeypatch)
    cards, card_func = _capture_cards()
    calc = _base_calc(zone_lookup="ZOP")

    indices_mod.render_indices_section(calc=calc, card_func=card_func)

    assert _find_value(cards, "Recuo Lateral") == "1.50 m"


def test_render_indices_section_formats_key_cards_from_rule(monkeypatch):
    _patch_streamlit(monkeypatch)
    cards, card_func = _capture_cards()
    calc = _base_calc(
        rule={
            "zone_sigla": "ZOP",
            "subzone_code": "PADRAO",
            "tp_min": 0.30,
            "to_max": 0.60,
            "to_sub_max": 0.60,
            "ia_max": 3.0,
            "ia_min": 0.2,
            "recuo_frontal_m": 3,
            "recuo_lateral_m": 1.5,
            "recuo_fundos_m": 3,
            "area_min_lote_m2": 250,
            "area_max_lote_m2": 62500,
            "testada_min_meio_m": 10,
            "testada_min_esquina_m": 12,
            "testada_max_m": 250,
            "gabarito_m": 72,
        },
        zone_lookup="ZOP",
    )

    indices_mod.render_indices_section(calc=calc, card_func=card_func)

    assert _find_value(cards, "Taxa de Permeabilidade (TP) mínima") == "30%"
    assert _find_value(cards, "Taxa de Ocupação (TO) máxima") == "60%"
    assert _find_value(cards, "TO do Subsolo máxima") == "60%"
    assert _find_value(cards, "Índice de Aproveitamento (IA) máximo") == "3"
    assert _find_value(cards, "Índice de Aproveitamento (IA) mínimo") == "0.20"
    assert _find_value(cards, "Testada mínima") == "Meio: 10 m | Esquina: 12 m"
    assert _find_value(cards, "Altura máxima (gabarito)") == "72 m"
    assert _find_value(cards, "Testada máxima") == "250 m"


def test_render_indices_section_fetches_rule_when_missing(monkeypatch):
    fake = _patch_streamlit(monkeypatch)
    cards, card_func = _capture_cards()
    calc = {"zone_lookup": "ZAP", "use_type_code": "RES_UNI", "subzone_code": "PADRAO"}

    def get_rule_func(**kwargs):
        assert kwargs["zone_sigla"] == "ZAP"
        assert kwargs["use_type_code"] == "RES_UNI"
        assert kwargs["subzone_code"] == "PADRAO"
        return {
            "zone_sigla": "ZAP",
            "subzone_code": "PADRAO",
            "tp_min": 0.25,
            "to_max": 0.65,
            "ia_max": 2.5,
            "recuo_frontal_m": 3,
            "recuo_lateral_m": 1.5,
            "recuo_fundos_m": 1.5,
        }

    indices_mod.render_indices_section(calc=calc, card_func=card_func, get_rule_func=get_rule_func)

    assert calc["rule"]["zone_sigla"] == "ZAP"
    assert _find_value(cards, "Zona") == "ZAP"


def test_render_indices_section_prefers_calc_subzone_over_rule_padrao(monkeypatch):
    _patch_streamlit(monkeypatch)
    cards, card_func = _capture_cards()
    calc = {
        "zone_lookup": "ZEIP",
        "use_type_code": "RES_MULTI_R21",
        "subzone_code": "ZEIP_3",
    }

    def get_rule_func(**kwargs):
        assert kwargs["zone_sigla"] == "ZEIP"
        assert kwargs["subzone_code"] == "ZEIP_3"
        return {
            "zone_sigla": "ZEIP",
            "subzone_code": "PADRAO",
            "tp_min": 0.15,
            "to_max": 0.70,
            "to_subsolo_max": 0.60,
            "ia_max": 2.0,
            "ia_min": 0.2,
            "recuo_frontal_m": 0,
            "recuo_lateral_m": 0,
            "recuo_fundos_m": 1.5,
            "area_min_lote_m2": 125,
            "testada_min_meio_m": 5,
            "gabarito_m": 8,
        }

    indices_mod.render_indices_section(calc=calc, card_func=card_func, get_rule_func=get_rule_func)

    assert _find_value(cards, "Subzona") == "ZEIP_3"
