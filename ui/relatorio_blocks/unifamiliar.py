from __future__ import annotations

from typing import Any, Dict

import pandas as pd
import streamlit as st

from .shared import (
    render_header_relatorio,
    render_tabela_localizacao,
    render_tabela_resultado_viabilidade,
    render_descricao_zona,
)


def _table(rows: list[tuple[str, str]], c1: str = "Regra", c2: str = "Valor") -> None:
    st.table(pd.DataFrame(rows, columns=[c1, c2]))


def render_tabela_resumo_rapido_unifamiliar(parametros: Dict[str, Any]) -> None:
    st.markdown("### 📏 4️⃣ Regras principais para este terreno")
    st.markdown("Depois de entender a zona, o próximo passo é ver as regras básicas do lote. Essas são as regras que mais impactam o projeto.")
    _table([
        ("TO máxima", str(parametros.get("to_max", "—"))),
        ("TP mínima", str(parametros.get("tp_min", "—"))),
        ("IA máximo", str(parametros.get("ia_max", "—"))),
        ("Altura máxima", str(parametros.get("altura_max", "—"))),
    ])


def render_tabela_regras_principais_unifamiliar(parametros: Dict[str, Any]) -> None:
    rows = [
        ("TO máxima", str(parametros.get("to_max", "—"))),
        ("TP mínima", str(parametros.get("tp_min", "—"))),
        ("IA máximo", str(parametros.get("ia_max", "—"))),
        ("IA mínimo", str(parametros.get("ia_min_texto", "—"))),
        ("Recuo frontal", str(parametros.get("recuo_frontal", "—"))),
        ("Recuo lateral", str(parametros.get("recuo_lateral_texto", "—"))),
        ("Recuo de fundos", str(parametros.get("recuo_fundos", "—"))),
        ("Altura máxima", str(parametros.get("altura_max", "—"))),
    ]
    _table(rows, "Parâmetro", "Valor")


def render_tabela_ocupacao_terreo_unifamiliar(dados: Dict[str, Any]) -> None:
    st.markdown("### 📐 5️⃣ Quanto posso ocupar no térreo?")
    st.markdown("A zona permite um limite de ocupação no térreo. Além da regra da zona, também vale olhar o que realmente cabe no lote depois de respeitar os recuos.")
    _table([
        ("Área do terreno", str(dados.get("area_terreno", "—"))),
        ("TO máxima", str(dados.get("to_max", "—"))),
        ("Área máxima pela TO", str(dados.get("area_to_max", "—"))),
    ], "Item", "Valor")
    st.markdown("**Opção 1 — Respeitando os recuos padrão**")
    _table([
        ("Recuo frontal", str(dados.get("recuo_frontal", "—"))),
        ("Recuo lateral", str(dados.get("recuo_lateral_texto", "—"))),
        ("Recuo de fundos", str(dados.get("recuo_fundos", "—"))),
        ("Largura útil", str(dados.get("largura_util", "—"))),
        ("Profundidade útil", str(dados.get("profundidade_util", "—"))),
        ("Área útil estimada", str(dados.get("area_implantacao_recuos", "—"))),
    ], "Item", "Valor")
    st.markdown("**Opção 2 — Implantação no alinhamento**")
    _table([
        ("Aplicável?", str(dados.get("implantacao_alinhamento_status", "—"))),
        ("Térreo máximo nessa opção", str(dados.get("area_max_alinhamento", "—"))),
    ], "Item", "Valor")


def render_tabela_permeabilidade_unifamiliar(dados: Dict[str, Any]) -> None:
    st.markdown("### 🌿 6️⃣ Quanto preciso deixar livre?")
    st.markdown("A zona exige uma parte do terreno com área permeável. Isso ajuda na absorção da água da chuva e influencia diretamente a ocupação possível.")
    _table([
        ("Área do terreno", str(dados.get("area_terreno", "—"))),
        ("TP mínima", str(dados.get("tp_min", "—"))),
        ("Área permeável mínima", str(dados.get("area_permeavel_min", "—"))),
    ], "Item", "Valor")
    st.table(pd.DataFrame([
        ["Opção 1", dados.get("area_ocupada_op1", "—"), dados.get("area_restante_op1", "—"), dados.get("area_permeavel_min", "—"), dados.get("area_impermeavel_op1", "—")],
        ["Opção 2", dados.get("area_ocupada_op2", "—"), dados.get("area_restante_op2", "—"), dados.get("area_permeavel_min", "—"), dados.get("area_impermeavel_op2", "—")],
    ], columns=["Cenário", "Área ocupada", "Área restante", "Deve ficar permeável", "Pode impermeabilizar"]))


def render_tabela_tipos_piso() -> None:
    st.markdown("### 🧱 7️⃣ Tipos de piso: o que conta como permeável?")
    st.markdown("Nem todo piso externo conta do mesmo jeito na permeabilidade. Isso ajuda a entender que nem toda área livre conta 100% como permeável.")
    st.table(pd.DataFrame([
        ["Grama", "100%"],
        ["Brita solta / terra batida", "100%"],
        ["Piso drenante", "90%"],
        ["Bloco de concreto vazado ('piso verde')", "60%"],
        ["Pedra portuguesa / intertravado", "25%"],
    ], columns=["Tipo de piso", "Percentual considerado permeável"]))


def render_tabela_ia_unifamiliar(dados: Dict[str, Any]) -> None:
    st.markdown("### 🏢 8️⃣ Posso construir mais andares?")
    st.markdown("Além do limite no térreo, existe o limite total permitido. Isso ajuda a entender o porte máximo da construção.")
    _table([
        ("Área do terreno", str(dados.get("area_terreno", "—"))),
        ("IA", str(dados.get("ia_max", "—"))),
        ("Área total máxima", str(dados.get("area_total_max", "—"))),
        ("Altura máxima", str(dados.get("altura_max", "—"))),
    ], "Item", "Valor")


def render_tabela_vagas_unifamiliar(dados: Dict[str, Any]) -> None:
    st.markdown("### 🚗 9️⃣ Preciso de vagas de estacionamento?")
    st.markdown("Para residência unifamiliar, normalmente não há exigência mínima obrigatória de vagas. Mesmo assim, vale conferir o caso concreto no licenciamento.")
    _table([
        ("Exigência mínima de vagas", str(dados.get("exige_vagas_texto", "—"))),
        ("Quantidade estimada", str(dados.get("qtd_vagas", "—"))),
    ], "Item", "Valor")


def render_relatorio_unifamiliar(contexto: Dict[str, Any]) -> None:
    render_header_relatorio("unifamiliar")
    render_tabela_localizacao(contexto["localizacao"])
    render_tabela_resultado_viabilidade(contexto["viabilidade"], "residência unifamiliar")
    render_descricao_zona(contexto["zona"])
    render_tabela_resumo_rapido_unifamiliar(contexto["parametros"])
    render_tabela_regras_principais_unifamiliar(contexto["parametros"])
    render_tabela_ocupacao_terreo_unifamiliar(contexto["ocupacao"])
    render_tabela_permeabilidade_unifamiliar(contexto["permeabilidade"])
    render_tabela_tipos_piso()
    render_tabela_ia_unifamiliar(contexto["ia"])
    render_tabela_vagas_unifamiliar(contexto["vagas"])
