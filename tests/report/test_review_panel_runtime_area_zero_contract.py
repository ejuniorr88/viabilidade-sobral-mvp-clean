from __future__ import annotations

import sys
import types
import importlib.util
from pathlib import Path
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


class StreamlitCapture(types.SimpleNamespace):
    def __init__(self):
        super().__init__()
        self.session_state = {}
        self._texts: list[str] = []

    def markdown(self, body, *args, **kwargs):
        if isinstance(body, str):
            self._texts.append(body)
        elif body is not None:
            self._texts.append(str(body))

    @contextmanager
    def _ctx(self):
        yield self

    def columns(self, spec):
        n = spec if isinstance(spec, int) else len(spec)
        return [self._ctx() for _ in range(n)]

    def dump(self) -> str:
        return "\n".join(self._texts)


def _render_review(monkeypatch, *, built_ground_value):
    path = Path(__file__).resolve().parents[2] / "ui" / "report" / "review_panel.py"
    spec = importlib.util.spec_from_file_location("review_panel_under_test", path)
    review_panel = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(review_panel)

    st = StreamlitCapture()
    st.session_state.update({"built_ground_m2": built_ground_value})
    monkeypatch.setattr(review_panel, "st", st, raising=False)

    review_panel.render_review_panel(
        calc={"zone": "ZEIP", "street_name": "Rua Teste"},
        session_snapshot={
            "lot_front_m": 10,
            "lot_depth_m": 30,
            "lot_area_m2": 300,
            "built_ground_m2": built_ground_value,
        },
    )
    return st.dump()


def test_review_panel_area_zero_renders_mandatory_hint(monkeypatch):
    text = _render_review(monkeypatch, built_ground_value=0)

    assert "Área construída pretendida" in text
    assert "Não informada" in text
    assert "Caso você ainda esteja fazendo um estudo em fase inicial" in text
    assert "área construída no térreo" in text
    assert "pode deixar o campo como 0" in text
    assert "potencial máximo permitido para o lote selecionado" in text
    assert "capacidade construtiva conforme os parâmetros urbanísticos aplicáveis" in text


def test_review_panel_positive_area_does_not_render_zero_hint(monkeypatch):
    text = _render_review(monkeypatch, built_ground_value=150)

    assert "150,00 m²" in text
    assert "Valor informado pelo usuário para a área construída pretendida" in text
    assert "pode deixar o campo como 0" not in text
    assert "potencial máximo permitido para o lote selecionado" not in text
