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
    return importlib.import_module('ui.relatorio_blocks.multifamiliar_items.item_06_ocupacao_terreo')



def test_item_06_uses_area_digitada_when_valid_and_within_to(monkeypatch):
    mod = _load_module(monkeypatch)
    outputs: list[str] = []
    monkeypatch.setattr(mod, 'md', outputs.append)

    ctx = {
        'lot_area_f': 300.0,
        'to_max_pct': 60.0,
        'to_m2': 180.0,
        'built_ground': 150.0,
        'A_recuos': 178.5,
        'rec_fr': 3.0,
        'rec_lat': 1.5,
        'rec_fun': 1.5,
        'W_util': 7.0,
        'D_util': 25.5,
        'multi_tipo': 'R2.2',
        'use_type_code': 'RES_MULTI_R22',
    }

    mod.render(ctx)
    joined = '\n'.join(outputs)
    assert 'Área pretendida informada pelo usuário' in joined
    assert 'ficando dentro do limite máximo da zona' in joined
    assert 'Como a área informada pelo usuário é inviável para este lote' not in joined



def test_item_06_falls_back_when_area_digitada_exceeds_to(monkeypatch):
    mod = _load_module(monkeypatch)
    outputs: list[str] = []
    monkeypatch.setattr(mod, 'md', outputs.append)

    ctx = {
        'lot_area_f': 300.0,
        'to_max_pct': 60.0,
        'to_m2': 180.0,
        'built_ground': 200.0,
        'A_recuos': 178.5,
        'rec_fr': 3.0,
        'rec_lat': 1.5,
        'rec_fun': 1.5,
        'W_util': 7.0,
        'D_util': 25.5,
        'multi_tipo': 'R2.2',
        'use_type_code': 'RES_MULTI_R22',
    }

    mod.render(ctx)
    joined = '\n'.join(outputs)
    assert 'ultrapassando o limite máximo da zona' in joined
    assert 'a análise passa a continuar considerando o limite máximo permitido pela zona' in joined
