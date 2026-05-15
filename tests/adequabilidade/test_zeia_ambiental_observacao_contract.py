"""Contratos para observação ambiental/documental exclusiva das ZEIAs.

Garante que:
- ZEIA-APP, ZEIA 1, ZEIA 2 e ZEIA 3 são reconhecidas como ZEIAs;
- a observação ambiental/documental aparece somente quando ZEIA permite pela via;
- ZEIA + via local/pedestre/compartilhada permanece pela zona e não recebe observação;
- zona não-ZEIA com PERMITE PELA VIA não recebe a observação das ZEIAs.
"""

from __future__ import annotations

import sys
import types

streamlit_stub = types.SimpleNamespace(
    markdown=lambda *args, **kwargs: None,
    session_state={},
)
sys.modules.setdefault("streamlit", streamlit_stub)

from ui.relatorio_blocks.multifamiliar_items import common


def _fake_fetch(*, zone_sigla: str, via_tipo_texto: str | None, use_type_code: str):
    via_norm = common._via_tipo_norm(via_tipo_texto)
    normalized_zone = (
        str(zone_sigla or "")
        .upper()
        .replace("-", "")
        .replace("/", "")
        .replace(" ", "")
    )

    zone_class = "I" if normalized_zone in {"ZEIAAPP", "ZEIA1", "ZEIA2", "ZEIA3"} else "AP"

    if via_norm in {
        "ARTERIAL",
        "COLETORA",
        "ARTERIAL_PAISAGISTICA",
        "COLETORA_PAISAGISTICA",
    }:
        via_class = "A"
    else:
        via_class = None

    return zone_class, via_class, {
        "zone_sigla_in": zone_sigla,
        "via_tipo_in": via_tipo_texto,
        "via_tipo_norm": via_norm,
        "use_type_code": use_type_code,
    }


def _build_ctx(zone: str, via_tipo: str):
    return common.build_context(
        calc={
            "multi_tipo": "R3",
            "use_type_code": "RES_MULTI_R3",
            "zone": zone,
            "zone_sigla": zone,
            "via_tipo": via_tipo,
            "lot_area_m2": 300,
        },
        rule=None,
        fetch_adequabilidade_fn=_fake_fetch,
    )


def test_reconhece_variacoes_de_zeia_para_observacao_exclusiva():
    assert common._is_zeia_zone("ZEIA-APP")
    assert common._is_zeia_zone("ZEIA APP")
    assert common._is_zeia_zone("ZEIA/APP")
    assert common._is_zeia_zone("ZEIA 1")
    assert common._is_zeia_zone("ZEIA1")
    assert common._is_zeia_zone("ZEIA 2")
    assert common._is_zeia_zone("ZEIA2")
    assert common._is_zeia_zone("ZEIA 3")
    assert common._is_zeia_zone("ZEIA3")
    assert not common._is_zeia_zone("ZEIS 1")
    assert not common._is_zeia_zone("ZOP")


def test_zeia_app_com_via_local_nao_permite_e_nao_exibe_observacao_pela_via():
    ctx = _build_ctx("ZEIA-APP", "via local")

    assert ctx["status_curto"] == "NÃO PERMITE"
    assert "área de interesse ambiental" not in ctx["explicacao"]
    assert "regularidade documental" not in ctx["explicacao"]
    assert "PERMITE PELA VIA" not in ctx["status_curto"]


def test_zeia_com_arterial_ou_coletora_exibe_observacao_ambiental_documental():
    for zona in ("ZEIA-APP", "ZEIA 1", "ZEIA 2", "ZEIA 3"):
        for via in ("via arterial_existente", "via coletora_existente"):
            ctx = _build_ctx(zona, via)

            assert ctx["status_curto"] == "PERMITE PELA VIA"
            assert "área de interesse ambiental" in ctx["explicacao"]
            assert "órgão municipal competente" in ctx["explicacao"]
            assert "restrições ambientais aplicáveis" in ctx["explicacao"]
            assert "regularidade documental do imóvel" in ctx["explicacao"]
            assert "matrícula, escritura, registro" in ctx["explicacao"]


def test_zeia_com_troncal_ou_regional_mantem_alerta_rodoviario_e_observacao_zeia():
    casos = [
        ("ZEIA-APP", "RODOVIA BR-222", "DNIT"),
        ("ZEIA 1", "via troncal", "DNIT"),
        ("ZEIA 2", "CE-362", "SOP/CE"),
        ("ZEIA 3", "via regional", "SOP/CE"),
    ]

    for zona, via, orgao in casos:
        ctx = _build_ctx(zona, via)

        assert ctx["status_curto"] == "PERMITE PELA VIA"
        assert orgao in ctx["explicacao"]
        assert "área de interesse ambiental" in ctx["explicacao"]
        assert "regularidade documental do imóvel" in ctx["explicacao"]


def test_observacao_zeia_nao_aparece_em_zona_nao_zeia_mesmo_permitindo_pela_via():
    ctx = _build_ctx("ZEIS 1", "via coletora_existente")

    assert ctx["status_curto"] == "PERMITE PELA VIA"
    assert "área de interesse ambiental" not in ctx["explicacao"]
    assert "regularidade documental do imóvel" not in ctx["explicacao"]
