from __future__ import annotations

import sys
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


def _rule_zeip(*, subzone_code: str, gabarito: float = 12.0) -> dict:
    return {
        "zone_sigla": "ZEIP",
        "subzone_code": subzone_code,
        "to_max_pct": 70.0,
        "tp_min_pct": 15.0,
        "ia_max": 2.0,
        "ia_min": 0.20,
        "recuo_frontal_m": 0.0,
        "recuo_lateral_m": 0.0,
        "recuo_fundos_m": 1.5,
        "gabarito_m": gabarito,
        "area_min_lote_m2": 125.0,
        "area_max_lote_m2": 40000.0,
        "testada_min_m": 5.0,
        "testada_max_m": 200.0,
    }


def _calc_multi(*, use_type_code: str, multi_tipo: str, subzone_code: str, lot_area: float, front: float, depth: float, via_tipo: str = "via local", built_ground=None, zone: str = "ZEIP") -> dict:
    calc = {
        "ok": True,
        "project_mode": "GUIA_FASE_1",
        "use_type_code": use_type_code,
        "multi_tipo": multi_tipo,
        "zone": zone,
        "zone_sigla": zone,
        "subzone_code": subzone_code,
        "lot_area_m2": lot_area,
        "lot_front_m": front,
        "lot_depth_m": depth,
        "via_nome": "Rua Teste",
        "via_tipo": via_tipo,
    }
    if built_ground is not None:
        calc["built_ground_m2"] = built_ground
    return calc


def _render_multifamiliar(monkeypatch, *, calc: dict, rule: dict, zone_class: str = "A", via_class=None) -> str:
    import ui.relatorio_blocks.multifamiliar_guia as guia
    from ui.relatorio_blocks.multifamiliar_items import common
    import ui.relatorio_blocks.quadro_tecnico as quadro_tecnico

    st = StreamlitCapture()
    st.session_state.update({"lot_is_corner": False, "built_ground_m2": calc.get("built_ground_m2", 0) or 0})

    monkeypatch.setattr(guia, "st", st, raising=False)
    monkeypatch.setattr(common, "st", st, raising=False)
    monkeypatch.setattr(quadro_tecnico, "st", st, raising=False)
    monkeypatch.setattr(
        guia,
        "_fetch_adequabilidade",
        lambda zone_sigla, via_tipo_texto, use_type_code: (zone_class, via_class, {}),
        raising=False,
    )

    guia.render_multifamiliar_guia(calc=calc, rule=rule)
    return st.dump()


def test_r3_zeip5_area_zero_render_blocks_forbidden_regressions(monkeypatch):
    text = _render_multifamiliar(
        monkeypatch,
        calc=_calc_multi(
            use_type_code="RES_MULTI_R3",
            multi_tipo="R3",
            subzone_code="ZEIP_5",
            lot_area=300,
            front=10,
            depth=30,
            built_ground=0,
        ),
        rule=_rule_zeip(subzone_code="ZEIP_5"),
    )

    required = [
        "R3 — residência multifamiliar vertical",
        "ZEIP — ZEIP 5",
        "Meio de quadra",
        "Área mínima do lote: 125,00 m²",
        "Área máxima do lote: 40.000,00 m²",
        "Testada mínima: 5,00 m",
        "Testada máxima: 200,00 m",
        "300,00 × 70,0% = 210,00",
        "Pelos recuos, a construção até caberia fisicamente em uma área de **285,00 m²**",
        "Porém, isso não significa que seja permitido ocupar tudo isso",
        "Taxa de Ocupação é mais restritiva e limita a ocupação do térreo a **210,00 m²**",
        "limite real de ocupação no térreo é **210,00 m²**",
        "300,00 − 210,00 = 90,00",
        "45,00 podem receber piso impermeável",
        "Por via:** via local — neste caso, não há sobreposição por via arterial/coletora",
    ]
    plain_text = _plain(text)
    for snippet in required:
        assert snippet.replace("**", "") in plain_text, f"Texto obrigatório sumiu ou foi alterado: {snippet}"

    forbidden = [
        "None",
        "Uso analisado: None",
        "Zona: —",
        "Tipo de lote: —",
        "envelope físico",
        "Se você utilizar **285,00** no térreo",
        "Se você utilizar 285,00 no térreo",
        "Área restante no lote: 300,00 − 285,00",
        "15,00 podem receber piso impermeável",
    ]
    for snippet in forbidden:
        assert snippet.replace("**", "") not in plain_text, f"Regressão proibida encontrada: {snippet}"


def test_r21_zeip7_testada_7_alerts_and_never_suggests_5_pavements(monkeypatch):
    text = _render_multifamiliar(
        monkeypatch,
        calc=_calc_multi(
            use_type_code="RES_MULTI_R21",
            multi_tipo="R2.1",
            subzone_code="ZEIP_7",
            lot_area=210,
            front=7,
            depth=30,
            built_ground=0,
        ),
        rule=_rule_zeip(subzone_code="ZEIP_7", gabarito=15.0),
    )

    required = [
        "R2.1 — 2 unidades no mesmo lote",
        "testada informada é menor que a referência usual de 8,00 m",
        "exige análise no licenciamento municipal",
        "frente e acesso independente para a via pública oficial",
        "paredes externas total ou parcialmente comuns",
        "máximo 2 pavimentos",
        "210,00 × 70,0% = 147,00",
        "Texto didático para R2.1",
        "Cenário A — unidades sobrepostas",
        "Cenário B — unidades lado a lado",
        "Taxa de Ocupação (TO)",
        "Taxa de Permeabilidade (TP)",
        "Índice de Aproveitamento (IA)",
        "Pelos recuos aplicáveis nessa leitura, a construção até caberia fisicamente em **199,50 m²**",
        "limite real de ocupação no térreo é **147,00 m²**",
        "cada unidade teria aproximadamente **73,50 m²**",
        "Resultado final: ⚠️ PERMITE COM RESSALVA — R2.1",
    ]
    plain_text = _plain(text)
    for snippet in required:
        assert snippet.replace("**", "") in plain_text, f"Texto obrigatório sumiu ou foi alterado: {snippet}"

    forbidden = [
        "5 pavimentos",
        "algo próximo de 5",
        "A largura original do lote é de 10,00 m",
        "10,00 − 0,00 − 0,00 = 7,00",
        "Se você utilizar **199,50** no térreo",
        "Área restante no lote: 210,00 − 199,50",
    ]
    for snippet in forbidden:
        assert snippet.replace("**", "") not in plain_text, f"Regressão proibida encontrada: {snippet}"


def test_r21_zam_uses_general_unifamiliar_logic_and_two_scenarios(monkeypatch):
    rule_zam = {
        "zone_sigla": "ZAM",
        "subzone_code": "PADRAO",
        "to_max_pct": 60.0,
        "tp_min_pct": 30.0,
        "ia_max": 1.5,
        "ia_min": None,
        "recuo_frontal_m": 3.0,
        "recuo_lateral_m": 1.5,
        "recuo_fundos_m": 1.5,
        "gabarito_m": 15.0,
        "area_min_lote_m2": 150.0,
        "area_max_lote_m2": 62500.0,
        "testada_min_m": 6.0,
        "testada_max_m": 250.0,
    }
    text = _render_multifamiliar(
        monkeypatch,
        calc=_calc_multi(
            use_type_code="RES_MULTI_R21",
            multi_tipo="R2.1",
            subzone_code="PADRAO",
            lot_area=300,
            front=10,
            depth=30,
            built_ground=0,
            zone="ZAM",
        ),
        rule=rule_zam,
    )
    plain_text = _plain(text)
    required = [
        "R2.1 é um multifamiliar, mas tem uma regra especial",
        "Taxa de Ocupação (TO)",
        "Taxa de Permeabilidade (TP)",
        "Índice de Aproveitamento (IA)",
        "300,00 × 60,0% = 180,00",
        "Pelos recuos aplicáveis nessa leitura, a construção até caberia fisicamente em 285,00 m²",
        "Taxa de Ocupação (TO), o limite do térreo é 180,00 m²",
        "limite real de ocupação no térreo é 180,00 m²",
        "Cenário A — unidades sobrepostas",
        "Cenário B — unidades lado a lado",
        "cada unidade teria aproximadamente 90,00 m²",
    ]
    for snippet in required:
        assert snippet in plain_text, f"Texto obrigatório do R2.1 geral/ZAM sumiu: {snippet}"

    forbidden = [
        "a área máxima do térreo dobra",
        "pode ocupar 285,00 m² no térreo",
        "5 pavimentos",
    ]
    for snippet in forbidden:
        assert snippet not in plain_text, f"Regressão proibida encontrada no R2.1 geral/ZAM: {snippet}"


def test_zeip9_r3_never_allows_simple_edificio_without_warning(monkeypatch):
    text = _render_multifamiliar(
        monkeypatch,
        calc=_calc_multi(
            use_type_code="RES_MULTI_R3",
            multi_tipo="R3",
            subzone_code="ZEIP_9",
            lot_area=200,
            front=10,
            depth=20,
            built_ground=0,
        ),
        rule=_rule_zeip(subzone_code="ZEIP_9"),
    )

    required = [
        "ZEIP 9",
        "R3 — residência multifamiliar vertical",
        "Atenção especial — ZEIP_9",
        "EXIGE CONFIRMAÇÃO — ZEIP_9",
        "restrição específica quanto à construção de novos edifícios",
        "não alteração da configuração dos lotes existentes",
        "200,00 × 70,0% = 140,00",
        "20,00 − recuo frontal − recuo de fundo = 18,50",
        "Pelos recuos, a construção até caberia fisicamente em uma área de **185,00 m²**",
        "limite real de ocupação no térreo é **140,00 m²**",
        "200,00 − 140,00 = 60,00",
    ]
    plain_text = _plain(text)
    for snippet in required:
        assert snippet.replace("**", "") in plain_text, f"Texto obrigatório sumiu ou foi alterado: {snippet}"

    forbidden = [
        "A profundidade original do lote é de 30,00 m",
        "30,00 − recuo frontal − recuo de fundo = 18,50",
        "Se você utilizar **185,00** no térreo",
        "Área restante no lote: 200,00 − 185,00",
        "Resultado final: ✅ PERMITE",
    ]
    for snippet in forbidden:
        assert snippet.replace("**", "") not in plain_text, f"Regressão proibida encontrada: {snippet}"
