from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _install_streamlit_stub() -> None:
    """Evita depender do Streamlit real para testar helpers puros do common.py."""
    if "streamlit" in sys.modules:
        return

    streamlit_stub = types.SimpleNamespace(
        markdown=lambda *args, **kwargs: None,
        json=lambda *args, **kwargs: None,
        warning=lambda *args, **kwargs: None,
        success=lambda *args, **kwargs: None,
        error=lambda *args, **kwargs: None,
        info=lambda *args, **kwargs: None,
        expander=lambda *args, **kwargs: _DummyContextManager(),
        session_state={},
    )
    sys.modules["streamlit"] = streamlit_stub


class _DummyContextManager:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _load_common_module():
    _install_streamlit_stub()

    repo_root = Path(__file__).resolve().parents[2]
    common_path = repo_root / "ui" / "relatorio_blocks" / "multifamiliar_items" / "common.py"
    spec = importlib.util.spec_from_file_location("multifamiliar_common_for_test", common_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_via_local_pedestre_compartilhada_nao_sobrepoem_zona():
    common = _load_common_module()

    for via_texto in ("via local", "via de pedestre", "via compartilhada"):
        assert common._via_tipo_norm(via_texto) is None

        icon, status, explicacao = common._summarize_adequabilidade(
            zone_class="I",
            via_norm=common._via_tipo_norm(via_texto),
            via_class=None,
        )

        assert icon == "❌"
        assert status == "NÃO PERMITE"
        assert "prevalece a regra da zona" in explicacao


def test_vias_arterial_e_coletora_sobrepoem_classificacao_da_zona_quando_via_for_a():
    common = _load_common_module()

    for via_texto in ("via arterial", "via arterial_existente", "via coletora", "via coletora_existente"):
        via_norm = common._via_tipo_norm(via_texto)
        assert via_norm in {"ARTERIAL", "COLETORA"}

        icon, status, explicacao = common._summarize_adequabilidade(
            zone_class="I",
            via_norm=via_norm,
            via_class="A",
        )

        assert icon == "✅"
        assert status == "PERMITE PELA VIA"
        assert "não fica limitada apenas à classificação indicada pela zona" in explicacao
        assert "Art. 99 da LC 91/2023" in explicacao


def test_vias_paisagisticas_sobrepoem_classificacao_da_zona_quando_via_for_a():
    common = _load_common_module()

    casos = {
        "via arterial paisagística": "ARTERIAL_PAISAGISTICA",
        "via coletora paisagística": "COLETORA_PAISAGISTICA",
    }

    for via_texto, esperado in casos.items():
        via_norm = common._via_tipo_norm(via_texto)
        assert via_norm == esperado

        icon, status, explicacao = common._summarize_adequabilidade(
            zone_class="I",
            via_norm=via_norm,
            via_class="A",
        )

        assert icon == "✅"
        assert status == "PERMITE PELA VIA"
        assert "não fica limitada apenas à classificação indicada pela zona" in explicacao


def test_via_troncal_ou_br_permite_pela_via_com_alerta_dnit_sem_texto_de_pequeno_porte_fixo():
    common = _load_common_module()

    for via_texto in ("via troncal", "RODOVIA BR-222", "BR 222", "rodovia federal"):
        via_norm = common._via_tipo_norm(via_texto)
        assert via_norm == "TRONCAL"

        icon, status, explicacao = common._summarize_adequabilidade(
            zone_class="I",
            via_norm=via_norm,
            via_class=None,
        )

        assert icon == "✅"
        assert status == "PERMITE PELA VIA"
        assert "DNIT" in explicacao
        assert "não fica limitada apenas à classificação indicada pela zona" in explicacao
        assert "não fica limitado apenas ao pequeno porte" not in explicacao


def test_via_regional_ou_ce_permite_pela_via_com_alerta_sop_sem_texto_de_pequeno_porte_fixo():
    common = _load_common_module()

    for via_texto in ("via regional", "CE-362", "CE 362", "rodovia estadual"):
        via_norm = common._via_tipo_norm(via_texto)
        assert via_norm == "REGIONAL"

        icon, status, explicacao = common._summarize_adequabilidade(
            zone_class="I",
            via_norm=via_norm,
            via_class=None,
        )

        assert icon == "✅"
        assert status == "PERMITE PELA VIA"
        assert "SOP/CE" in explicacao
        assert "não fica limitada apenas à classificação indicada pela zona" in explicacao
        assert "não fica limitado apenas ao pequeno porte" not in explicacao
