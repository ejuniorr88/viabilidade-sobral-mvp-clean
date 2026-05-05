from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMMON = ROOT / "ui" / "relatorio_blocks" / "multifamiliar_items" / "common.py"


def _txt() -> str:
    return COMMON.read_text(encoding="utf-8")


def test_status_zona_e_via_existe_no_summarizer() -> None:
    txt = _txt()
    assert "PERMITE PELA ZONA E PELA VIA" in txt
    assert "Análise pela zona e pela via" in txt
    assert "zona e também pela classificação da via" in txt


def test_status_apenas_pela_via_mantem_explicacao_de_sobreposicao() -> None:
    txt = _txt()
    assert "PERMITE PELA VIA" in txt
    assert "zona, isoladamente, não indicou permissão plena" in txt
    assert "regra de sobreposição da adequabilidade pela via" in txt


def test_fallback_residencial_forca_zonas_simples_para_a() -> None:
    txt = _txt()
    assert "def _fallback_zone_class_residencial" in txt
    for zone in ("ZAM", "ZAP", "ZCR", "ZOP"):
        assert f'"{zone}"' in txt
    assert 'zone_fallback_previous_class' in txt
    assert '_norm(zone_class) != fallback_zone_class' in txt


def test_fallback_residencial_preserva_zeia_zepe_como_nao_permitidas_por_zona() -> None:
    txt = _txt()
    assert '"ZEPE"' in txt
    assert '"ZEIA"' in txt
    assert 'return "I"' in txt


def test_summarizer_diferencia_zona_e_via_de_apenas_via(monkeypatch) -> None:
    # Evita depender do Streamlit real durante import do módulo.
    fake_streamlit = types.SimpleNamespace(markdown=lambda *a, **k: None)
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    mod = importlib.import_module("ui.relatorio_blocks.multifamiliar_items.common")

    icon, status, msg = mod._summarize_adequabilidade(
        zone_class="A",
        via_norm="COLETORA",
        via_class="A",
    )
    assert icon == "✅"
    assert status == "PERMITE PELA ZONA E PELA VIA"
    assert "zona e pela via" in msg

    icon2, status2, msg2 = mod._summarize_adequabilidade(
        zone_class="I",
        via_norm="COLETORA",
        via_class="A",
    )
    assert icon2 == "✅"
    assert status2 == "PERMITE PELA VIA"
    assert "zona, isoladamente" in msg2
