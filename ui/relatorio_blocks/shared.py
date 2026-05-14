from __future__ import annotations

from typing import Any, Dict

import pandas as pd
import streamlit as st


def _table(rows: list[tuple[str, str]], c1: str = "Campo", c2: str = "Valor") -> None:
    st.table(pd.DataFrame(rows, columns=[c1, c2]))


def render_header_relatorio(tipo_relatorio: str) -> None:
    titulo = "🏡 RELATÓRIO URBANÍSTICO" if tipo_relatorio == "unifamiliar" else "🏢 RELATÓRIO URBANÍSTICO — MULTIFAMILIAR"
    st.markdown(f"## {titulo}")
    st.markdown(
        "Este relatório mostra, de forma simples, o que pode ou não pode ser feito no terreno informado, com base na zona, na via e nas regras urbanísticas do município."
    )


def render_tabela_localizacao(dados_localizacao: Dict[str, Any]) -> None:
    st.markdown("### 📍 1️⃣ Onde está localizado o terreno?")
    st.markdown("Aqui estão os dados principais usados nesta análise. Essas informações são a base de todo o relatório.")
    rows = [
        ("Uso informado", str(dados_localizacao.get("uso_label", "—"))),
        ("Área do terreno", str(dados_localizacao.get("area_terreno", "—"))),
        ("Dimensões", str(dados_localizacao.get("dimensoes", "—"))),
        ("Zona", str(dados_localizacao.get("zona", "—"))),
        ("Subzona / setor", str(dados_localizacao.get("subzona", "—"))),
        ("Tipo de lote", str(dados_localizacao.get("tipo_lote", "—"))),
        ("Via", str(dados_localizacao.get("nome_via", "—"))),
        ("Tipo de via", str(dados_localizacao.get("tipo_via", "—"))),
    ]
    _table(rows)


def render_tabela_resultado_viabilidade(resultado: Dict[str, Any], titulo_uso: str) -> None:
    st.markdown(f"### ✅ 2️⃣ Esse uso de {titulo_uso} pode ser feito aqui?")
    st.markdown(
        "Primeiro olhamos a zona em que o terreno está localizado. Em alguns casos, a via também entra nessa análise e pode reforçar ou limitar o que pode ser feito no local."
    )
    rows = [
        ("Por zona", str(resultado.get("resultado_zona", "—"))),
        ("Por via", str(resultado.get("resultado_via", "—"))),
        ("Resumo final", str(resultado.get("resultado_final", "—"))),
    ]
    _table(rows, "Verificação", "Resultado")
    st.caption(str(resultado.get("texto_apoio", "Resultado inicial para leitura rápida.")))


def render_descricao_zona(dados_zona: Dict[str, Any]) -> None:
    st.markdown("### 🧭 3️⃣ O que essa zona quer dizer?")
    st.markdown(
        "A zona identificada para o terreno ajuda a entender quais regras urbanísticas se aplicam ao lote. Ela orienta o uso permitido, a ocupação máxima no térreo, a área permeável mínima, os recuos, a altura e outros cuidados do projeto."
    )
    rows = [
        ("Zona", str(dados_zona.get("zona_nome_completo") or dados_zona.get("zona") or "—")),
        ("O que é", str(dados_zona.get("zona_texto_o_que_e", "—"))),
        ("Na prática", str(dados_zona.get("zona_texto_pratico", "—"))),
        ("Via do terreno", str(dados_zona.get("nome_via", "—"))),
        ("Tipo de via", str(dados_zona.get("tipo_via", "—"))),
    ]
    _table(rows, "Item", "Descrição")


def render_fechamento_final(tipo_relatorio: str) -> None:
    st.markdown("### ✅ Encerramento")
    st.markdown("Este relatório é uma análise inicial para ajudar a entender o potencial urbanístico do terreno.")
    st.caption("Ele não representa aprovação automática da Prefeitura e não substitui alvará, licença, certidão, parecer técnico ou análise oficial do órgão competente.")
