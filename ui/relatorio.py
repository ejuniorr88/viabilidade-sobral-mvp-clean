"""Seção do relatório (texto final para o usuário copiar/colar).

⚠️ Histórico do bug:
Este módulo estava com um erro de sintaxe (um bloco solto começando com `*, calc: ...`)
que fazia o import `from ui.relatorio import render_relatorio_section` falhar e,
consequentemente, derrubava o app.

Abaixo está uma versão estável e simples do relatório.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st


def _fmt_num(v: Any, nd: int = 2) -> str:
    try:
        return f"{float(v):.{nd}f}"
    except Exception:
        return "-"


def render_relatorio_section(
    *,
    zone_sigla: str,
    via_tipo: str,
    lote: Optional[Dict[str, float]] = None,
    calc: Optional[Dict[str, Any]] = None,
    rule: Optional[Dict[str, Any]] = None,
    street_info: Optional[Dict[str, Any]] = None,
    zoning_info: Optional[Dict[str, Any]] = None,
) -> None:
    """Renderiza o relatório final em formato de texto (copiar/colar)."""

    lote = lote or {}
    calc = calc or {}
    rule = rule or {}

    st.subheader("6) Relatório Urbanístico")

    with st.expander("Dados usados no relatório (debug)", expanded=False):
        st.json(
            {
                "zone_sigla": zone_sigla,
                "via_tipo": via_tipo,
                "lote": lote,
                "calc": calc,
                "rule": rule,
                "street_info": street_info,
                "zoning_info": zoning_info,
            }
        )

    st.markdown(
        f"""
### Relatório de Viabilidade Urbanística

**Zona:** {zone_sigla}  
**Tipo de via:** {via_tipo}

#### Dados do lote
- Área do terreno: {_fmt_num(lote.get('area'))} m²
- Testada: {_fmt_num(lote.get('testada'))} m
- Profundidade: {_fmt_num(lote.get('profundidade'))} m

#### Índices (Supabase)
- Taxa de Ocupação (TO) máx: {_fmt_num(calc.get('to_max_pct'))}%
- Taxa Permeável (TP) mín: {_fmt_num(calc.get('tp_min_pct'))}%
- Índice de Aproveitamento (IA) máx: {_fmt_num(calc.get('ia_max'))}

#### Recuos (m)
- Frontal: {_fmt_num(calc.get('front_setback_m'))}
- Lateral: {_fmt_num(calc.get('side_setback_m'))}
- Fundo: {_fmt_num(calc.get('rear_setback_m'))}
"""
    )
