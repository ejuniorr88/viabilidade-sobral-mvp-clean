
from __future__ import annotations

from typing import Any, Dict

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


def render_tabela_tipos_via_multifamiliar() -> None:
    rows = [
        ("Via local", "Rua de bairro, normalmente usada mais para acesso local."),
        ("Via coletora", "Recolhe o tráfego das vias locais e leva para vias maiores."),
        ("Via arterial", "Via principal, com fluxo maior e papel importante na circulação."),
        ("Via paisagística", "Via com tratamento urbano ou paisagístico específico."),
    ]
    import streamlit as st
    st.markdown("### Tipos de via")
    st.markdown(_md_table(("Tipo de via", "Leitura simples"), rows))


def render_tabela_siglas_adequabilidade() -> None:
    import streamlit as st
    st.markdown("### Siglas de adequabilidade")
    rows = [
        ("A", "Adequado / permitido", "Pode seguir com o projeto, respeitando as demais regras."),
        ("I", "Inadequado / não permitido", "Em regra, não pode nesse local/condição."),
        ("AP", "Adequado pequeno porte", "Pode, mas normalmente limitado ao porte pequeno."),
        ("AM", "Adequado médio porte", "Pode, mas normalmente limitado ao porte médio."),
        ("AP/AM", "Depende do porte", "Pode, mas depende se o caso é pequeno ou médio."),
        ("PE", "Projeto especial", "Pode exigir análise específica e condições extras no licenciamento."),
    ]
    st.markdown(_md_table(("Sigla", "O que significa", "Como interpretar"), rows))


def render_tabela_portes_multifamiliar() -> None:
    import streamlit as st
    st.markdown("### Portes")
    rows = [
        ("Pequeno", "até 250 m²"),
        ("Médio", "de 250,01 m² até 1.000 m²"),
        ("Grande", "de 1.000,01 m² até 5.000 m²"),
        ("Projeto especial", "acima de 5.000 m²"),
    ]
    st.markdown(_md_table(("Porte", "Faixa (área construída total)"), rows))


def render_tabela_parametros_inicio_multifamiliar(parametros: Dict[str, Any]) -> None:
    import streamlit as st
    st.markdown("### Parâmetros iniciais")
    rows = [
        ("TO máxima", parametros.get("to_max")),
        ("TP mínima", parametros.get("tp_min")),
        ("IA máximo", parametros.get("ia_max")),
        ("Altura máxima", parametros.get("altura_max")),
        ("Observação", "Demais recuos, altura e testadas seguem a regra carregada para a zona analisada."),
    ]
    st.markdown(_md_table(("Parâmetro", "Valor"), rows))


def render_tabela_tipo_escolhido_multifamiliar(tipo_multifamiliar: str) -> None:
    import streamlit as st
    st.markdown("### Tipo multifamiliar escolhido")
    t = str(tipo_multifamiliar or "").strip().upper()
    if t == "R2.2":
        rows = [
            ("Tipo", "condomínio horizontal"),
            ("Organização", "unidades com acesso por via interna"),
            ("Atenção", "verificar áreas comuns, acessos e condições da zona"),
            ("Observação", "pode exigir conferência de quadra máxima"),
        ]
    elif t == "R3":
        rows = [
            ("Tipo", "condomínio vertical"),
            ("Atenção", "altura, circulação, áreas comuns, vagas e acessos"),
            ("Observação", "pode exigir conferência de quadra máxima"),
        ]
    else:
        rows = [
            ("Tipo", "2 unidades no mesmo lote (justapostas ou sobrepostas)"),
            ("Altura / andares", "no máximo 2 pavimentos"),
            ("Testada mínima se justaposto", "8,00 m"),
            ("Observação", "em ZEIS, a regra específica da zona pode prevalecer"),
        ]
    st.markdown(_md_table(("Item", "Regra"), rows))


def render_tabela_vagas_multifamiliar() -> None:
    import streamlit as st
    st.markdown("### Vagas multifamiliares")
    st.markdown(_md_table(("Situação", "Exigência"), [
        ("Apartamento com menos de 90 m²", "1 vaga por unidade"),
        ("Apartamento com 90 m² ou mais", "1,5 vaga por unidade"),
    ]))
    st.markdown(_md_table(("Exemplo", "Resultado"), [
        ("10 apartamentos com 80 m²", "10 vagas"),
        ("11 apartamentos com 100 m²", "11 × 1,5 = 16,5 → 17 vagas"),
    ]))
    st.markdown(_md_table(("Tema", "Texto"), [
        ("Arredondamento", "quando aparecer 1,5, o total final deve ser arredondado para cima"),
        ("Atenção", "em R2.2 e R3, pode ser necessária verificação de quadra máxima da zona"),
    ]))


def render_relatorio_multifamiliar(contexto: Dict[str, Any]) -> None:
    render_header_relatorio("multifamiliar")
    render_tabela_localizacao(contexto.get("localizacao", {}))
    render_tabela_resultado_viabilidade(contexto.get("viabilidade", {}), "residência multifamiliar")
    render_descricao_zona(contexto.get("zona", {}))
    render_tabela_tipos_via_multifamiliar()
    render_tabela_siglas_adequabilidade()
    render_tabela_portes_multifamiliar()
    render_tabela_parametros_inicio_multifamiliar(contexto.get("parametros", {}))
    render_tabela_tipo_escolhido_multifamiliar(contexto.get("tipo_multifamiliar", "R2.1"))
    render_tabela_vagas_multifamiliar()
    render_tabela_dicas_finais()
    render_tabela_ambientes()
    render_tabela_observacoes_ambientes()
    render_tabela_figuras_calcada(contexto.get("rule", {}))
    render_fechamento_final("multifamiliar")
