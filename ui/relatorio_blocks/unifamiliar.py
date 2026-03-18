
from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from .shared import (
    render_header_relatorio,
    render_tabela_localizacao,
    render_tabela_resultado_viabilidade,
    render_descricao_zona,
    render_tabela_ambientes,
    render_tabela_observacoes_ambientes,
    render_tabela_figuras_calcada,
    render_tabela_dicas_finais,
    render_fechamento_final,
)


def _fmt(v: Any) -> str:
    if v is None or v == "":
        return "—"
    return str(v)


def _md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(_fmt(v) for v in row) + " |")
    return "\n".join(out)


def render_tabela_resumo_rapido_unifamiliar(parametros: Dict[str, Any]) -> None:
    st.markdown("### 📏 4️⃣ Regras principais para este terreno")
    rows = [
        ("TO máxima", parametros.get("to_max")),
        ("TP mínima", parametros.get("tp_min")),
        ("IA máximo", parametros.get("ia_max")),
        ("Altura máxima", parametros.get("altura_max")),
    ]
    st.markdown(_md_table(("Regra", "Valor"), rows))


def render_tabela_regras_principais_unifamiliar(parametros: Dict[str, Any]) -> None:
    rows = [
        ("TO máxima", parametros.get("to_max")),
        ("TP mínima", parametros.get("tp_min")),
        ("IA máximo", parametros.get("ia_max")),
        ("IA mínimo", parametros.get("ia_min_texto")),
        ("Recuo frontal", parametros.get("recuo_frontal")),
        ("Recuo lateral", parametros.get("recuo_lateral_texto")),
        ("Recuo de fundos", parametros.get("recuo_fundos")),
        ("Altura máxima", parametros.get("altura_max")),
    ]
    st.markdown(_md_table(("Parâmetro", "Valor"), rows))


def render_tabela_ocupacao_terreo_unifamiliar(dados: Dict[str, Any]) -> None:
    st.markdown("### 📐 5️⃣ Quanto posso ocupar no térreo?")
    rows1 = [
        ("Área do terreno", dados.get("area_terreno")),
        ("TO máxima", dados.get("to_max")),
        ("Área máxima pela TO", dados.get("area_to_max")),
    ]
    st.markdown(_md_table(("Item", "Valor"), rows1))
    rows2 = [
        ("Recuo frontal", dados.get("recuo_frontal")),
        ("Recuo lateral", dados.get("recuo_lateral_texto")),
        ("Recuo de fundos", dados.get("recuo_fundos")),
        ("Largura útil", dados.get("largura_util")),
        ("Profundidade útil", dados.get("profundidade_util")),
        ("Área útil estimada", dados.get("area_implantacao_recuos")),
    ]
    st.markdown(_md_table(("Item", "Valor"), rows2))
    rows3 = [
        ("Aplicável?", dados.get("implantacao_alinhamento_status")),
        ("Térreo máximo nessa opção", dados.get("area_max_alinhamento")),
    ]
    st.markdown(_md_table(("Item", "Valor"), rows3))


def render_tabela_permeabilidade_unifamiliar(dados: Dict[str, Any]) -> None:
    st.markdown("### 🌿 6️⃣ Quanto preciso deixar livre?")
    rows1 = [
        ("Área do terreno", dados.get("area_terreno")),
        ("TP mínima", dados.get("tp_min")),
        ("Área permeável mínima", dados.get("area_permeavel_min")),
    ]
    st.markdown(_md_table(("Item", "Valor"), rows1))
    rows2 = [
        ("Opção 1", dados.get("area_ocupada_op1"), dados.get("area_restante_op1"), dados.get("area_permeavel_min"), dados.get("area_impermeavel_op1")),
        ("Opção 2", dados.get("area_ocupada_op2"), dados.get("area_restante_op2"), dados.get("area_permeavel_min"), dados.get("area_impermeavel_op2")),
    ]
    st.markdown(_md_table(("Cenário", "Área ocupada", "Área restante", "Deve ficar permeável", "Pode impermeabilizar"), rows2))


def render_tabela_tipos_piso() -> None:
    st.markdown("### 🧱 7️⃣ Tipos de piso: o que conta como permeável?")
    rows = [
        ("Grama", "100%"),
        ("Brita solta / terra batida", "100%"),
        ("Piso drenante", "90%"),
        ("Bloco de concreto vazado (“piso verde”)", "60%"),
        ("Pedra portuguesa / intertravado", "25%"),
    ]
    st.markdown(_md_table(("Tipo de piso", "Percentual considerado permeável"), rows))


def render_tabela_ia_unifamiliar(dados: Dict[str, Any]) -> None:
    st.markdown("### 🏢 8️⃣ Posso construir mais andares?")
    rows = [
        ("Área do terreno", dados.get("area_terreno")),
        ("IA", dados.get("ia_max")),
        ("Área total máxima", dados.get("area_total_max")),
        ("Altura máxima", dados.get("altura_max")),
    ]
    st.markdown(_md_table(("Item", "Valor"), rows))


def render_tabela_vagas_unifamiliar(dados: Dict[str, Any]) -> None:
    st.markdown("### 🚗 9️⃣ Preciso de vagas de estacionamento?")
    rows = [
        ("Exigência mínima de vagas", dados.get("exige_vagas_texto")),
        ("Quantidade estimada", dados.get("qtd_vagas")),
    ]
    st.markdown(_md_table(("Item", "Valor"), rows))


def render_relatorio_unifamiliar(contexto: Dict[str, Any]) -> None:
    render_header_relatorio("unifamiliar")
    render_tabela_localizacao(contexto.get("localizacao", {}))
    render_tabela_resultado_viabilidade(contexto.get("viabilidade", {}), "residência unifamiliar")
    render_tabela_resumo_rapido_unifamiliar(contexto.get("parametros", {}))
    render_descricao_zona(contexto.get("zona", {}))
    render_tabela_regras_principais_unifamiliar(contexto.get("parametros", {}))
    render_tabela_ocupacao_terreo_unifamiliar(contexto.get("ocupacao", {}))
    render_tabela_permeabilidade_unifamiliar(contexto.get("permeabilidade", {}))
    render_tabela_tipos_piso()
    render_tabela_ia_unifamiliar(contexto.get("ia", {}))
    render_tabela_vagas_unifamiliar(contexto.get("vagas", {}))
    render_tabela_ambientes()
    render_tabela_observacoes_ambientes()
    render_tabela_figuras_calcada(contexto.get("rule", {}))
    render_tabela_dicas_finais()
    render_fechamento_final("unifamiliar")
