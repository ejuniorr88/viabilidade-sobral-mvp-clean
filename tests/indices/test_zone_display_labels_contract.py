from __future__ import annotations

from pathlib import Path

from core.zone_display_labels import (
    display_label,
    format_testada_minima,
    normalize_subzone_code,
    normalize_zone_sigla,
    special_notice,
)


def test_normalize_zone_sigla_accepts_zeia_app_variants() -> None:
    assert normalize_zone_sigla("ZEIA-APP") == "ZEIA_APP"
    assert normalize_zone_sigla("ZEIA APP") == "ZEIA_APP"
    assert normalize_zone_sigla("ZEIA/APP") == "ZEIA_APP"
    assert normalize_zone_sigla("ZEIP") == "ZEIP"


def test_normalize_subzone_code_defaults_to_padrao() -> None:
    assert normalize_subzone_code(None) == "PADRAO"
    assert normalize_subzone_code("") == "PADRAO"
    assert normalize_subzone_code("ZEIP_1") == "ZEIP_1"


def test_display_label_preserves_fallback_without_label() -> None:
    assert display_label({}, "recuo_frontal_m", "0 m") == "0 m"


def test_display_label_uses_official_label_when_available() -> None:
    labels = {"recuo_frontal_m": "Não permitido"}
    assert display_label(labels, "recuo_frontal_m", "—") == "Não permitido"


def test_format_testada_minima_uses_official_labels() -> None:
    labels = {
        "testada_min_meio_m": "**",
        "testada_min_esquina_m": "**",
    }
    assert format_testada_minima(labels, meio_fallback="—", esquina_fallback="—") == "Meio: ** | Esquina: **"


def test_special_notice_returns_none_when_missing() -> None:
    assert special_notice({}) is None


def test_special_notice_returns_text_when_present() -> None:
    labels = {"special_notice": "Não são permitidas alterações/configurações dos lotes existentes."}
    assert special_notice(labels) == "Não são permitidas alterações/configurações dos lotes existentes."


def test_indices_section_contains_official_display_legend_table() -> None:
    source = Path("ui/indices/section.py").read_text(encoding="utf-8")
    assert "Legenda dos parâmetros" in source
    assert "indices-legend-table" in source
    assert "Símbolo / Texto" in source
    assert "Significado" in source
    assert "Parâmetro especial sujeito" in source
    assert "Parâmetro sem valor numérico fixo" in source
    assert "Não permitido" in source
    assert "Não se aplica" in source
