from __future__ import annotations

import sys
import types
from contextlib import contextmanager


def _install_import_stubs() -> None:
    st_stub = sys.modules.get("streamlit")
    if st_stub is None:
        st_stub = types.ModuleType("streamlit")
        sys.modules["streamlit"] = st_stub
    st_stub.session_state = getattr(st_stub, "session_state", {})
    st_stub.secrets = getattr(st_stub, "secrets", {})
    st_stub.cache_resource = getattr(st_stub, "cache_resource", lambda *args, **kwargs: (lambda fn: fn))
    st_stub.cache_data = getattr(st_stub, "cache_data", lambda *args, **kwargs: (lambda fn: fn))
    st_stub.markdown = getattr(st_stub, "markdown", lambda *args, **kwargs: None)
    st_stub.subheader = getattr(st_stub, "subheader", lambda *args, **kwargs: None)
    st_stub.info = getattr(st_stub, "info", lambda *args, **kwargs: None)
    st_stub.warning = getattr(st_stub, "warning", lambda *args, **kwargs: None)
    st_stub.error = getattr(st_stub, "error", lambda *args, **kwargs: None)
    st_stub.success = getattr(st_stub, "success", lambda *args, **kwargs: None)
    st_stub.caption = getattr(st_stub, "caption", lambda *args, **kwargs: None)
    st_stub.write = getattr(st_stub, "write", lambda *args, **kwargs: None)
    st_stub.table = getattr(st_stub, "table", lambda *args, **kwargs: None)
    st_stub.image = getattr(st_stub, "image", lambda *args, **kwargs: None)
    st_stub.json = getattr(st_stub, "json", lambda *args, **kwargs: None)
    if not hasattr(st_stub, "columns"):
        st_stub.columns = lambda spec: []
    if not hasattr(st_stub, "expander"):
        @contextmanager
        def _expander(*args, **kwargs):
            yield st_stub
        st_stub.expander = _expander

    if "streamlit.components" not in sys.modules:
        comp_pkg = types.ModuleType("streamlit.components")
        sys.modules["streamlit.components"] = comp_pkg
    if "streamlit.components.v1" not in sys.modules:
        comp_v1 = types.ModuleType("streamlit.components.v1")
        comp_v1.html = lambda *args, **kwargs: None
        sys.modules["streamlit.components.v1"] = comp_v1

    if "supabase" not in sys.modules:
        supabase_stub = types.ModuleType("supabase")
        supabase_stub.Client = object
        supabase_stub.create_client = lambda *args, **kwargs: object()
        sys.modules["supabase"] = supabase_stub


_install_import_stubs()

def _plain(text: str) -> str:
    return text.replace("**", "").replace("__", "")


class StreamlitCapture(types.SimpleNamespace):
    def __init__(self):
        super().__init__()
        self.session_state = {}
        self.secrets = {}
        self._texts: list[str] = []
        self.cache_resource = lambda show_spinner=False: (lambda fn: fn)

    def _push(self, value):
        if isinstance(value, str):
            self._texts.append(value)
        elif value is not None:
            self._texts.append(str(value))

    def markdown(self, body, *args, **kwargs):
        self._push(body)

    def subheader(self, body, *args, **kwargs):
        self._push(body)

    def info(self, body, *args, **kwargs):
        self._push(body)

    def warning(self, body, *args, **kwargs):
        self._push(body)

    def error(self, body, *args, **kwargs):
        self._push(body)

    def success(self, body, *args, **kwargs):
        self._push(body)

    def caption(self, body, *args, **kwargs):
        self._push(body)

    def write(self, body, *args, **kwargs):
        self._push(body)

    def table(self, body, *args, **kwargs):
        self._push(body)

    def image(self, *args, **kwargs):
        self._push("[image]")

    def json(self, body, *args, **kwargs):
        self._push(body)

    @contextmanager
    def expander(self, *args, **kwargs):
        yield self

    @contextmanager
    def _ctx(self):
        yield self

    def columns(self, spec):
        n = spec if isinstance(spec, int) else len(spec)
        return [self._ctx() for _ in range(n)]

    def dump(self) -> str:
        return "\n".join(self._texts)


def _rule_zeip5() -> dict:
    return {
        "zone_sigla": "ZEIP",
        "subzone_code": "ZEIP_5",
        "to_max_pct": 70.0,
        "tp_min_pct": 15.0,
        "ia_max": 2.0,
        "ia_min": 0.20,
        "recuo_frontal_m": 0.0,
        "recuo_lateral_m": 0.0,
        "recuo_fundos_m": 1.5,
        "gabarito_m": 12.0,
        "area_min_lote_m2": 125.0,
        "area_max_lote_m2": 40000.0,
        "testada_min_m": 5.0,
        "testada_max_m": 200.0,
    }


def _calc_uni(*, built_ground: float) -> dict:
    return {
        "ok": True,
        "project_mode": "GUIA_FASE_1",
        "use_type_code": "RES_UNI",
        "zone": "ZEIP",
        "zone_sigla": "ZEIP",
        "subzone_code": "ZEIP_5",
        "lot_area_m2": 300,
        "lot_front_m": 10,
        "lot_depth_m": 30,
        "via_nome": "Rua Teste",
        "via_tipo": "via local",
        "built_ground_m2": built_ground,
        "rule": _rule_zeip5(),
    }


def _render_unifamiliar(monkeypatch, *, built_ground: float) -> str:
    import ui.relatorio as relatorio
    from ui.relatorio_blocks.unifamiliar_items import common as item_common
    import ui.relatorio_blocks.quadro_tecnico as quadro_tecnico

    st = StreamlitCapture()
    st.session_state.update(
        {
            "lot_is_irregular": False,
            "lot_is_corner": False,
            "lot_front_m": 10.0,
            "lot_depth_m": 30.0,
            "built_ground_m2": built_ground,
        }
    )

    monkeypatch.setattr(relatorio, "st", st, raising=False)
    monkeypatch.setattr(item_common, "st", st, raising=False)
    monkeypatch.setattr(quadro_tecnico, "st", st, raising=False)

    from ui.relatorio_blocks.unifamiliar_items import (
        item_01_localizacao, item_02_adequabilidade, item_03_leitura_adequabilidade,
        item_04_zona, item_05_regras_principais, item_06_ocupacao_terreo,
        item_07_permeabilidade, item_08_tipos_piso, item_09_ia_altura,
        item_10_vagas, item_11_quadro_tecnico, item_12_calcada,
        item_13_dicas, item_14_resumo, item_15_pos_etapa, item_16_fechamento,
    )
    for _mod in (
        item_01_localizacao, item_02_adequabilidade, item_03_leitura_adequabilidade,
        item_04_zona, item_05_regras_principais, item_06_ocupacao_terreo,
        item_07_permeabilidade, item_08_tipos_piso, item_09_ia_altura,
        item_10_vagas, item_11_quadro_tecnico, item_12_calcada,
        item_13_dicas, item_14_resumo, item_15_pos_etapa, item_16_fechamento,
    ):
        monkeypatch.setattr(_mod, "st", st, raising=False)
    monkeypatch.setattr(relatorio, "_fetch_adequabilidade_unifamiliar", lambda zone_sigla, via_tipo_texto: ("A", None, {}), raising=False)
    monkeypatch.setattr(
        relatorio,
        "fetch_zone_description",
        lambda zone_sigla, subzone_code=None, zone_label=None: {"title": "ZEIP 5"},
        raising=False,
    )
    monkeypatch.setattr(relatorio, "render_figuras_anexo_v", lambda rule, is_corner=False: st.markdown("[FIGURAS ANEXO V]"), raising=False)

    relatorio.render_relatorio_section(_calc_uni(built_ground=built_ground))
    return st.dump()


def test_unifamiliar_area_230_exceeds_to_but_not_recuos(monkeypatch):
    text = _render_unifamiliar(monkeypatch, built_ground=230)

    required = [
        "Área pretendida informada: **230,00 m²**",
        "ultrapassa o limite máximo permitido pela Taxa de Ocupação (TO)",
        "Taxa de Ocupação (TO) correspondente à área pretendida",
        "76,7%",
        "cabe fisicamente pelos recuos, mas não pode ser adotada porque ultrapassa a Taxa de Ocupação (TO) máxima",
        "referência de ocupação máxima no térreo continua sendo **210,00 m²**",
        "o projeto precisaria ser reduzido para respeitar esse limite",
    ]
    plain_text = _plain(text)
    for snippet in required:
        assert snippet.replace("**", "") in plain_text, f"Texto obrigatório sumiu ou foi alterado: {snippet}"

    forbidden = [
        "ultrapassa não apenas a TO máxima",
        "ultrapassa o limite físico de implantação com recuos",
        "ou **285,00 m²** caso sejam adotados os recuos",
        "ou 285,00 m² caso sejam adotados os recuos",
    ]
    for snippet in forbidden:
        assert snippet.replace("**", "") not in plain_text, f"Regressão proibida encontrada: {snippet}"


def test_unifamiliar_area_150_normal_case_keeps_expected_summary(monkeypatch):
    text = _render_unifamiliar(monkeypatch, built_ground=150)

    required = [
        "Área pretendida informada: **150,00 m²**",
        "abaixo do limite máximo permitido",
        "Taxa de Ocupação (TO) correspondente à área pretendida",
        "50,0%",
        "área pretendida de **150,00 m²** é viável",
        "área remanescente sem ocupação no térreo",
        "150,00 m²",
        "105,00 m²",
        "saldo estimado pelo **Índice de Aproveitamento (IA)**",
        "450,00 m²",
    ]
    plain_text = _plain(text)
    for snippet in required:
        assert snippet.replace("**", "") in plain_text, f"Texto obrigatório sumiu ou foi alterado: {snippet}"

    forbidden = [
        "ultrapassa o limite máximo permitido pela Taxa de Ocupação (TO)",
        "não é urbanisticamente possível",
        "Área pretendida informada: **230,00 m²**",
    ]
    for snippet in forbidden:
        assert snippet.replace("**", "") not in plain_text, f"Regressão proibida encontrada: {snippet}"
