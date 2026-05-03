"""Contratos para adequabilidade por vias troncal/regional e exceções.

Garante que:
- via local, via de pedestre e via compartilhada NÃO sobrepõem a zona;
- via arterial/coletora e paisagísticas continuam aplicando leitura pela via;
- via troncal/BR aplica leitura favorável com alerta DNIT;
- via regional/CE aplica leitura favorável com alerta SOP/CE.
"""

import sys
import types

streamlit_stub = types.SimpleNamespace(
    markdown=lambda *args, **kwargs: None,
    session_state={},
)
sys.modules.setdefault("streamlit", streamlit_stub)

from ui.relatorio_blocks.multifamiliar_items.common import (
    _summarize_adequabilidade,
    _via_tipo_norm,
)


def test_vias_sem_sobreposicao_preservam_regra_da_zona():
    for via_texto in ("via local", "via de pedestre", "via compartilhada"):
        via_norm = _via_tipo_norm(via_texto)
        assert via_norm is None

        icon, status, explicacao = _summarize_adequabilidade(
            zone_class="AP",
            via_norm=via_norm,
            via_class=None,
        )

        assert icon == "✅"
        assert status == "PERMITE SOMENTE PEQUENO PORTE"
        assert "apenas como pequeno porte" in explicacao


def test_arterial_coletora_e_paisagisticas_continuam_sobrepondo_pela_via():
    casos = {
        "via arterial_existente": "ARTERIAL",
        "via coletora_existente": "COLETORA",
        "via arterial_paisagistica_existente": "ARTERIAL_PAISAGISTICA",
        "via coletora_paisagistica_existente": "COLETORA_PAISAGISTICA",
    }

    for via_texto, esperado in casos.items():
        via_norm = _via_tipo_norm(via_texto)
        assert via_norm == esperado

        icon, status, explicacao = _summarize_adequabilidade(
            zone_class="AP",
            via_norm=via_norm,
            via_class="A",
        )

        assert icon == "✅"
        assert status == "PERMITE PELA VIA"
        assert "via permite o uso de forma mais ampla" in explicacao
        assert "Art. 99 da LC 91/2023" in explicacao


def test_via_troncal_e_br_permite_pela_via_com_alerta_dnit():
    for via_texto in ("via troncal", "RODOVIA BR-222", "BR 222", "rodovia federal"):
        via_norm = _via_tipo_norm(via_texto)
        assert via_norm == "TRONCAL"

        icon, status, explicacao = _summarize_adequabilidade(
            zone_class="AP",
            via_norm=via_norm,
            via_class=None,
        )

        assert icon == "✅"
        assert status == "PERMITE PELA VIA"
        assert "DNIT" in explicacao
        assert "rodovia federal" in explicacao.lower() or "br" in explicacao.lower()
        assert "não fica limitado apenas ao pequeno porte" in explicacao


def test_via_regional_e_ce_permite_pela_via_com_alerta_sop_ce():
    for via_texto in ("via regional", "CE-362", "CE 362", "rodovia estadual"):
        via_norm = _via_tipo_norm(via_texto)
        assert via_norm == "REGIONAL"

        icon, status, explicacao = _summarize_adequabilidade(
            zone_class="AP",
            via_norm=via_norm,
            via_class=None,
        )

        assert icon == "✅"
        assert status == "PERMITE PELA VIA"
        assert "SOP/CE" in explicacao
        assert "rodovia estadual" in explicacao.lower() or "ce" in explicacao.lower()
        assert "não fica limitado apenas ao pequeno porte" in explicacao
