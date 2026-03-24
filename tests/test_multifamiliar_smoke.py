import sys
import types
from contextlib import contextmanager
from pathlib import Path

if "streamlit" not in sys.modules:
    streamlit_stub = types.ModuleType("streamlit")
    streamlit_stub.session_state = {}
    streamlit_stub.secrets = {}
    streamlit_stub.cache_resource = lambda show_spinner=False: (lambda fn: fn)
    streamlit_stub.markdown = lambda *args, **kwargs: None
    streamlit_stub.subheader = lambda *args, **kwargs: None
    streamlit_stub.info = lambda *args, **kwargs: None
    streamlit_stub.warning = lambda *args, **kwargs: None
    streamlit_stub.error = lambda *args, **kwargs: None
    streamlit_stub.success = lambda *args, **kwargs: None
    streamlit_stub.caption = lambda *args, **kwargs: None
    streamlit_stub.write = lambda *args, **kwargs: None
    streamlit_stub.table = lambda *args, **kwargs: None
    streamlit_stub.image = lambda *args, **kwargs: None
    streamlit_stub.json = lambda *args, **kwargs: None
    @contextmanager
    def _expander(*args, **kwargs):
        yield streamlit_stub
    streamlit_stub.expander = _expander
    sys.modules["streamlit"] = streamlit_stub

if "supabase" not in sys.modules:
    supabase_stub = types.ModuleType("supabase")
    supabase_stub.Client = object
    supabase_stub.create_client = lambda *args, **kwargs: object()
    sys.modules["supabase"] = supabase_stub

ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


class StreamlitCapture:
    def __init__(self):
        self.session_state = {}
        self.texts = []

    def _push(self, value):
        if isinstance(value, str):
            self.texts.append(value)

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

    class _DummyCtx:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def columns(self, spec):
        n = spec if isinstance(spec, int) else len(spec)
        return [self._DummyCtx() for _ in range(n)]

    def table(self, body, *args, **kwargs):
        self.texts.append(str(body))

    def image(self, *args, **kwargs):
        self.texts.append("[image]")

    def json(self, body, *args, **kwargs):
        self.texts.append(str(body))

    @contextmanager
    def expander(self, *args, **kwargs):
        yield self

    def dump(self) -> str:
        return "\n".join(self.texts)


def test_multifamiliar_shared_sections_exist_and_keep_order() -> None:
    txt = _read("ui/relatorio_blocks/multifamiliar_guia.py")

    ordered = [
        "### 🚗 9️⃣ Vagas de estacionamento",
        "### 🚶 1️⃣1️⃣ O que preciso saber sobre a calçada?",
        "### 💡 1️⃣2️⃣ Dicas valiosas",
        "### 📌 1️⃣3️⃣ Resumo rápido final",
        "### 🏛️ 1️⃣4️⃣ O que acontece depois desta etapa?",
        "### ✅ 1️⃣5️⃣ Fechamento final",
    ]

    positions = []
    for anchor in ordered:
        count = txt.count(anchor)
        assert count >= 1, f"Âncora compartilhada obrigatória sumiu do multifamiliar: {anchor}"
        idx = txt.find(anchor)
        positions.append(idx)

    assert positions == sorted(positions), "As seções finais compartilhadas do multifamiliar perderam a ordem esperada."


def test_multifamiliar_nothing_reappears_after_fechamento_final() -> None:
    txt = _read("ui/relatorio_blocks/multifamiliar_guia.py")
    fechamento = "### ✅ 1️⃣5️⃣ Fechamento final"
    idx = txt.find(fechamento)
    assert idx != -1, "Fechamento final não encontrado no multifamiliar."

    tail = txt[idx + len(fechamento):]

    forbidden_after_end = [
        "Dicas valiosas",
        "Vagas de estacionamento",
        "O que preciso saber sobre a calçada?",
        "Quais medidas mínimas os ambientes precisam ter?",
        "Abrir em tamanho real",
        "Anexo V",
    ]
    for anchor in forbidden_after_end:
        assert anchor not in tail, (
            f"Nada do relatório deve reaparecer depois do Fechamento final. Encontrado: {anchor}"
        )


def test_multifamiliar_alvara_block_exists_before_fechamento() -> None:
    txt = _read("ui/relatorio_blocks/multifamiliar_guia.py")

    alvara = "### 🏛️ 1️⃣4️⃣ O que acontece depois desta etapa?"
    fechamento = "### ✅ 1️⃣5️⃣ Fechamento final"

    idx_alvara = txt.find(alvara)
    idx_fech = txt.find(fechamento)

    assert idx_alvara != -1, "Bloco do alvará não encontrado no multifamiliar."
    assert idx_fech != -1, "Fechamento final não encontrado no multifamiliar."
    assert idx_alvara < idx_fech, "O bloco do alvará precisa ficar antes do Fechamento final."


def test_multifamiliar_rendered_output_enforces_unique_final_headings(monkeypatch) -> None:
    import core.zone_descriptions as zone_descriptions
    import ui.relatorio_blocks.figuras_anexo_v as figuras_anexo_v
    import ui.relatorio_blocks.multifamiliar_guia as multifamiliar_guia
    import ui.relatorio_blocks.quadro_tecnico as quadro_tecnico

    st = StreamlitCapture()
    st.session_state.update({"lot_is_corner": False})

    monkeypatch.setattr(multifamiliar_guia, "st", st, raising=False)
    monkeypatch.setattr(quadro_tecnico, "st", st, raising=False)
    monkeypatch.setattr(figuras_anexo_v, "st", st, raising=False)
    monkeypatch.setattr(
        multifamiliar_guia,
        "_fetch_adequabilidade",
        lambda **kwargs: ("A", None, {"source": "test"}),
        raising=False,
    )
    monkeypatch.setattr(
        zone_descriptions,
        "fetch_zone_description",
        lambda zone_sigla, subzone_code=None, zone_label=None: {"title": "Zona de Adensamento Médio", "description_text": "Texto de teste"},
        raising=False,
    )
    monkeypatch.setattr(
        figuras_anexo_v,
        "render_figuras_anexo_v",
        lambda rule, is_corner=False: st.markdown("[FIGURAS ANEXO V]"),
        raising=False,
    )

    calc = {
        "multi_tipo": "R3",
        "use_type_code": "RES_MULTI_R3",
        "zone": "ZAM",
        "zone_sigla": "ZAM",
        "subzone_code": "PADRAO",
        "via_nome": "Rua Exemplo",
        "via_tipo": "Local",
        "lot_area_m2": 300,
        "lot_front_m": 10,
        "lot_depth_m": 30,
        "project_mode": "GUIA_FASE_1",
    }
    rule = {
        "to_max_pct": 60,
        "tp_min_pct": 30,
        "ia_max": 1.5,
        "recuo_frontal_m": 3.0,
        "recuo_lateral_m": 1.5,
        "recuo_fundos_m": 1.5,
        "gabarito_m": 15,
    }

    multifamiliar_guia.render_multifamiliar_guia(calc=calc, rule=rule)
    dumped = st.dump()

    required_once = [
        "### 🚗 9️⃣ Vagas de estacionamento",
        "### 📋 1️⃣0️⃣ Quais medidas mínimas os ambientes precisam ter?",
        "### 🚶 1️⃣1️⃣ O que preciso saber sobre a calçada?",
        "### 🏛️ 1️⃣4️⃣ O que acontece depois desta etapa?",
    ]
    for anchor in required_once:
        assert dumped.count(anchor) == 1, f"Heading duplicado no output final do multifamiliar: {anchor}"

    ordered = [
        "### 🚗 9️⃣ Vagas de estacionamento",
        "### 📋 1️⃣0️⃣ Quais medidas mínimas os ambientes precisam ter?",
        "### 🚶 1️⃣1️⃣ O que preciso saber sobre a calçada?",
        "### 💡 1️⃣2️⃣ Dicas valiosas",
        "### 📌 1️⃣3️⃣ Resumo rápido final",
        "### 🏛️ 1️⃣4️⃣ O que acontece depois desta etapa?",
        "### ✅ 1️⃣5️⃣ Fechamento final",
    ]
    positions = [dumped.find(anchor) for anchor in ordered]
    assert all(pos != -1 for pos in positions), "Output final do multifamiliar perdeu headings obrigatórios."
    assert positions == sorted(positions), "Ordem final do output renderizado do multifamiliar foi alterada."
