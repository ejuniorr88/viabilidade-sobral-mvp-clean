from __future__ import annotations

from typing import Any, Dict

import pandas as pd
import streamlit as st

from .shared import render_header_relatorio, render_tabela_localizacao, render_tabela_resultado_viabilidade, render_descricao_zona


def _table(rows: list[tuple[str, str]], c1: str = "Item", c2: str = "Valor") -> None:
    st.table(pd.DataFrame(rows, columns=[c1, c2]))


def render_tabela_tipos_via_multifamiliar() -> None:
    st.markdown("### Tipos de via (leitura simples)")
    st.table(pd.DataFrame([
        ["Via local", "Rua de bairro, normalmente usada mais para acesso local."],
        ["Via coletora", "Recolhe o tráfego das vias locais e leva para vias maiores."],
        ["Via arterial", "Via principal, com fluxo maior e papel importante na circulação."],
        ["Via paisagística", "Via com tratamento urbano ou paisagístico específico."],
    ], columns=["Tipo de via", "Leitura simples"]))


def render_tabela_siglas_adequabilidade() -> None:
    st.markdown("### Siglas de adequabilidade")
    st.table(pd.DataFrame([
        ["A", "Adequado / permitido", "Pode seguir com o projeto, respeitando as demais regras."],
        ["I", "Inadequado / não permitido", "Em regra, não pode nesse local/condição."],
        ["AP", "Adequado pequeno porte", "Pode, mas normalmente limitado ao porte pequeno."],
        ["AM", "Adequado médio porte", "Pode, mas normalmente limitado ao porte médio."],
        ["AP/AM", "Depende do porte", "Pode, mas depende se o caso é pequeno ou médio."],
        ["PE", "Projeto especial", "Pode exigir análise específica e condições extras no licenciamento."],
    ], columns=["Sigla", "O que significa", "Como interpretar"]))


def render_tabela_portes_multifamiliar() -> None:
    st.markdown("### Portes do multifamiliar")
    st.table(pd.DataFrame([
        ["Pequeno", "até 250 m²"],
        ["Médio", "de 250,01 m² até 1.000 m²"],
        ["Grande", "de 1.000,01 m² até 5.000 m²"],
        ["Projeto especial", "acima de 5.000 m²"],
    ], columns=["Porte", "Faixa (área construída total)"]))


def render_tabela_parametros_inicio_multifamiliar(parametros: Dict[str, Any]) -> None:
    st.markdown("### Parâmetros iniciais")
    _table([
        ("Taxa de Ocupação (TO) máxima", str(parametros.get("to_max", "—"))),
        ("Taxa de Permeabilidade (TP) mínima", str(parametros.get("tp_min", "—"))),
        ("Índice de Aproveitamento (IA) máximo", str(parametros.get("ia_max", "—"))),
        ("Altura máxima", str(parametros.get("altura_max", "—"))),
        ("Observação", "Demais recuos, altura e testadas seguem a regra carregada para a zona analisada."),
    ], "Parâmetro", "Valor")


def render_tabela_tipo_escolhido_multifamiliar(tipo_multifamiliar: str) -> None:
    tipo = str(tipo_multifamiliar or "R2.1")
    if tipo == "R2.2":
        rows = [("Tipo", "condomínio horizontal"), ("Organização", "unidades com acesso por via interna"), ("Atenção", "verificar áreas comuns, acessos e condições da zona"), ("Observação", "pode exigir conferência de quadra máxima")]
    elif tipo == "R3":
        rows = [("Tipo", "condomínio vertical"), ("Atenção", "altura, circulação, áreas comuns, vagas e acessos"), ("Observação", "pode exigir conferência de quadra máxima")]
    else:
        rows = [("Tipo", "2 unidades no mesmo lote (justapostas ou sobrepostas)"), ("Altura / andares", "no máximo 2 pavimentos"), ("Testada mínima se justaposto", "8,00 m"), ("Observação", "em ZEIS, a regra específica da zona pode prevalecer")]
    st.markdown("### Tipo escolhido")
    _table(rows)


def render_tabela_vagas_multifamiliar() -> None:
    st.markdown("### Vagas de estacionamento")
    st.table(pd.DataFrame([
        ["Apartamento com menos de 90 m²", "1 vaga por unidade"],
        ["Apartamento com 90 m² ou mais", "1,5 vaga por unidade"],
    ], columns=["Situação", "Exigência"]))
    st.table(pd.DataFrame([
        ["10 apartamentos com 80 m²", "10 vagas"],
        ["11 apartamentos com 100 m²", "11 × 1,5 = 16,5 → 17 vagas"],
    ], columns=["Exemplo", "Resultado"]))


def render_relatorio_multifamiliar(contexto: Dict[str, Any]) -> None:
    render_header_relatorio("multifamiliar")
    render_tabela_localizacao(contexto["localizacao"])
    render_tabela_resultado_viabilidade(contexto["viabilidade"], "residência multifamiliar")
    render_descricao_zona(contexto["zona"])
    render_tabela_tipos_via_multifamiliar()
    render_tabela_siglas_adequabilidade()
    render_tabela_portes_multifamiliar()
    render_tabela_parametros_inicio_multifamiliar(contexto["parametros"])
    render_tabela_tipo_escolhido_multifamiliar(contexto["tipo_multifamiliar"])
    render_tabela_vagas_multifamiliar()
