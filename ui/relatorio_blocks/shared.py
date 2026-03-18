
from __future__ import annotations

from typing import Any, Dict, Iterable, Sequence

import streamlit as st

from .dicas_valiosas import render_dicas_valiosas
from .figuras_anexo_v import render_figuras_anexo_v


def _fmt(v: Any) -> str:
    if v is None or v == "":
        return "—"
    return str(v)


def _md_table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(_fmt(v) for v in row) + " |")
    return "\n".join(out)


def render_header_relatorio(tipo_relatorio: str) -> None:
    tipo = str(tipo_relatorio or "").strip().lower()
    if tipo == "multifamiliar":
        st.subheader("🏢 RELATÓRIO URBANÍSTICO — MULTIFAMILIAR")
    else:
        st.subheader("🏡 RELATÓRIO URBANÍSTICO")
    st.markdown(
        "Este relatório mostra, de forma simples, o que pode ou não pode ser feito no terreno informado, "
        "com base na zona, na via e nas regras urbanísticas do município."
    )


def render_tabela_localizacao(dados_localizacao: Dict[str, Any]) -> None:
    st.markdown("### 📍 1️⃣ Onde está localizado o terreno?")
    rows = [
        ("Uso informado", dados_localizacao.get("uso_label")),
        ("Área do terreno", dados_localizacao.get("area_terreno")),
        ("Dimensões", dados_localizacao.get("dimensoes")),
        ("Zona", dados_localizacao.get("zona")),
        ("Subzona / setor", dados_localizacao.get("subzona")),
        ("Tipo de lote", dados_localizacao.get("tipo_lote")),
        ("Via", dados_localizacao.get("nome_via")),
        ("Tipo de via", dados_localizacao.get("tipo_via")),
    ]
    st.markdown(_md_table(("Campo", "Valor"), rows))


def render_tabela_resultado_viabilidade(resultado: Dict[str, Any], titulo_uso: str) -> None:
    st.markdown(f"### ✅ 2️⃣ Esse uso de {titulo_uso} pode ser feito aqui?")
    rows = [
        ("Por zona", resultado.get("resultado_zona")),
        ("Por via", resultado.get("resultado_via")),
        ("Resumo final", resultado.get("resultado_final")),
    ]
    st.markdown(_md_table(("Verificação", "Resultado"), rows))
    texto = resultado.get("texto_apoio")
    if texto:
        st.caption(str(texto))


def render_descricao_zona(dados_zona: Dict[str, Any]) -> None:
    st.markdown("### 🧭 3️⃣ O que essa zona quer dizer?")
    rows = [
        ("Zona", f"{_fmt(dados_zona.get('zona'))} — {_fmt(dados_zona.get('zona_nome_completo'))}"),
        ("O que é", dados_zona.get("zona_texto_o_que_e")),
        ("Na prática", dados_zona.get("zona_texto_pratico")),
        ("Via do terreno", dados_zona.get("nome_via")),
        ("Tipo de via", dados_zona.get("tipo_via")),
    ]
    st.markdown(_md_table(("Item", "Descrição"), rows))


def render_tabela_ambientes() -> None:
    st.markdown("### 📋 🔟 Quais medidas mínimas os ambientes precisam ter?")
    rows = [
        ("Sala de estar", "2,00 m", "8,00 m²", "1/8", "1/12", "2,50 m", "7"),
        ("Sala de jantar", "2,00 m", "6,00 m²", "1/8", "1/12", "2,50 m", "7"),
        ("Cozinha", "1,80 m", "5,00 m²", "1/8", "1/12", "2,50 m", "1-7"),
        ("1º e 2º quartos", "2,00 m", "8,00 m²", "1/8", "1/12", "2,50 m", "—"),
        ("Demais quartos", "2,00 m", "5,00 m²", "1/8", "1/12", "2,50 m", "—"),
        ("Banheiro", "1,00 m", "1,50 m²", "1/10", "1/16", "2,20 m", "1-2-3"),
        ("Área de serviço", "1,20 m", "1,80 m²", "1/10", "1/16", "2,20 m", "1-2-7"),
        ("Garagem", "2,20 m", "9,00 m²", "1/14", "1/24", "2,20 m", "7"),
        ("Escada", "0,80 m", "—", "—", "—", "2,10 m", "8-11-12-13"),
    ]
    st.markdown(_md_table(("Ambiente", "Círculo inscrito", "Área mínima", "Iluminação", "Ventilação", "Pé-direito", "Obs."), rows))


def render_tabela_observacoes_ambientes() -> None:
    st.markdown("### Observações aplicáveis")
    rows = [
        ("1", "Tolera-se iluminação e ventilação zenital."),
        ("2", "Admite-se ventilação mecânica ou indireta nos casos permitidos."),
        ("3", "Banheiro não pode comunicar-se diretamente com cozinha ou sala de jantar."),
        ("4", "Corredores com mais de 5,00 m devem ter largura mínima de 1,00 m."),
        ("5", "Corredores com mais de 10,00 m exigem ventilação mínima proporcional."),
        ("6", "Área de porta com veneziana pode ser computada como ventilação."),
        ("7", "Escadas devem ser de material incombustível ou tratado."),
        ("8", "Patamar obrigatório quando houver mudança de direção ou altura superior a 2,90 m."),
        ("9", "Largura mínima do degrau: 0,25 m."),
        ("10", "Altura máxima do degrau: 0,19 m."),
    ]
    st.markdown(_md_table(("Observação", "Texto"), rows))


def render_tabela_figuras_calcada(rule: Dict[str, Any] | None = None) -> None:
    st.markdown("### 🚶 1️⃣1️⃣ O que preciso saber sobre a calçada?")
    rows = [
        ("Figura 1", "Padrão de calçada; pode conter escadas e rampas; altura livre 2,10 m; declividade da calçada 2% ou 3%; rampa 5–20%."),
        ("Figura 2", "Calçada com largura superior a 2,00 m e inferior a 2,30 m; faixa de acesso, faixa livre, faixa de serviço; possibilidade de reduzir até 1,20 m."),
    ]
    st.markdown(_md_table(("Figura", "Descrição"), rows))
    if rule:
        render_figuras_anexo_v(rule)


def render_tabela_dicas_finais() -> None:
    st.markdown("### 💡 1️⃣2️⃣ Dicas importantes")
    render_dicas_valiosas()


def render_fechamento_final(tipo_relatorio: str) -> None:
    st.markdown(
        _md_table(
            ("Item", "Texto"),
            [
                ("Encerramento", "Este relatório foi pensado para ajudar você a entender o terreno de forma mais simples."),
                ("Observação final", "Na etapa de projeto e aprovação, ainda será preciso conferir os detalhes completos no licenciamento."),
            ],
        )
    )
