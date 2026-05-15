from __future__ import annotations

import importlib
import sys
import types


class _DummyStreamlit(types.ModuleType):
    def __init__(self):
        super().__init__('streamlit')
        self._info_messages: list[str] = []

    def info(self, text):
        self._info_messages.append(text)



def _load_module(monkeypatch):
    st_mod = _DummyStreamlit()
    monkeypatch.setitem(sys.modules, 'streamlit', st_mod)
    return importlib.import_module('ui.relatorio_blocks.multifamiliar_items.item_07_permeabilidade')



def test_item_07_uses_area_digitada_when_valid_and_within_to(monkeypatch):
    mod = _load_module(monkeypatch)
    outputs: list[str] = []
    monkeypatch.setattr(mod, 'md', outputs.append)

    ctx = {
        'lot_area_f': 300.0,
        'tp_min_pct': 30.0,
        'to_m2': 180.0,
        'A_recuos': 178.5,
        'built_ground': 150.0,
    }

    mod.render(ctx)
    joined = '\n'.join(outputs)
    assert 'Cálculo usando a área digitada pelo usuário' in joined
    assert 'a análise da permeabilidade passa a considerar esse valor' in joined
    assert 'Cenário 1 — usando o máximo da TO' not in joined



def test_item_07_keeps_fallback_when_area_digitada_exceeds_to(monkeypatch):
    mod = _load_module(monkeypatch)
    outputs: list[str] = []
    monkeypatch.setattr(mod, 'md', outputs.append)

    ctx = {
        'lot_area_f': 300.0,
        'tp_min_pct': 30.0,
        'to_m2': 180.0,
        'A_recuos': 178.5,
        'built_ground': 200.0,
    }

    mod.render(ctx)
    joined = '\n'.join(outputs)
    assert 'ultrapassa a **Taxa de Ocupação (TO)** máxima permitida' in joined
    assert 'relatório adota **178,50 m²** como limite de referência no térreo' in joined
    assert 'Cenário 1 — usando o máximo da TO' not in joined
    assert 'Cenário 2 — usando a implantação pelos recuos da zona' not in joined
