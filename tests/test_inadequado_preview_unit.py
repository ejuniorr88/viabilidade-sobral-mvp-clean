from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path


class _DummyExpander:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _DummyStreamlit(types.ModuleType):
    def __init__(self):
        super().__init__('streamlit')
        self.session_state = {}

    def expander(self, *args, **kwargs):
        return _DummyExpander()

    def json(self, *args, **kwargs):
        return None

    def markdown(self, *args, **kwargs):
        return None

    def error(self, *args, **kwargs):
        return None

    def info(self, *args, **kwargs):
        return None

    def warning(self, *args, **kwargs):
        return None



def _install_stubs(monkeypatch):
    st_mod = _DummyStreamlit()
    monkeypatch.setitem(sys.modules, 'streamlit', st_mod)

    zone_mod = types.ModuleType('core.zone_descriptions')
    zone_mod.fetch_zone_description = lambda *args, **kwargs: None
    monkeypatch.setitem(sys.modules, 'core.zone_descriptions', zone_mod)
    return st_mod



def test_should_block_report_returns_true_when_ctx_status_is_nao_permite(monkeypatch):
    _install_stubs(monkeypatch)
    mod = importlib.import_module('ui.relatorio_blocks.inadequado_preview')
    monkeypatch.setattr(mod, '_is_multifamiliar', lambda calc: False)
    monkeypatch.setattr(mod, '_build_unifamiliar_ctx', lambda calc: {'status_curto': 'NÃO PERMITE'})

    calc = {'zone': 'ZEPE1', 'use_type_code': 'RES_UNI'}
    assert mod.should_block_report(calc) is True
    assert mod.st.session_state[mod.DEBUG_SESSION_KEY]['stage'] == 'should_block_report'



def test_should_block_report_returns_false_and_stores_exception_payload(monkeypatch):
    _install_stubs(monkeypatch)
    mod = importlib.import_module('ui.relatorio_blocks.inadequado_preview')
    monkeypatch.setattr(mod, '_is_multifamiliar', lambda calc: False)
    monkeypatch.setattr(mod, '_build_unifamiliar_ctx', lambda calc: (_ for _ in ()).throw(RuntimeError('boom')))

    calc = {'zone': 'ZEPE1', 'zone_sigla': 'ZEPE1', 'subzone_code': 'PADRAO', 'use_type_code': 'RES_UNI', 'via_tipo': 'via local'}
    assert mod.should_block_report(calc) is False
    snap = mod.st.session_state[mod.DEBUG_SESSION_KEY]
    assert snap['stage'] == 'should_block_report_exception'
    assert snap['error'] == 'boom'
