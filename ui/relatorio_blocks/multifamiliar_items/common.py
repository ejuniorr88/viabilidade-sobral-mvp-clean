
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, List

import math
import streamlit as st

from ui.relatorio_blocks.terreno_irregular import is_irregular_context
from urban_rules.zone_profiles import (
    apply_zone_result_policy,
    is_zeis as _profile_is_zeis,
    zone_context_warnings,
)


def md(text: str) -> None:
    st.markdown(text)


def md_table(headers: list[str], rows: list[list[str]]) -> None:
    if not headers:
        return

    table = "<table style='width:100%; border-collapse: collapse;'>"
    table += "<thead><tr>"
    for h in headers:
        table += (
            "<th style='text-align:left; padding:8px; border:1px solid #ddd;'>"
            f"{h}</th>"
        )
    table += "</tr></thead><tbody>"

    for row in rows:
        table += "<tr>"
        for cell in row:
            table += (
                "<td style='padding:8px; border:1px solid #ddd;'>"
                f"{cell}</td>"
            )
        table += "</tr>"

    table += "</tbody></table>"
    st.markdown(table, unsafe_allow_html=True)


def fmt_num(v: Any, dec: int = 2) -> str:
    return _fmt_num(v, dec)


def fmt_pct(v: Any, dec: int = 1) -> str:
    return _fmt_pct(v, dec)



def _get_supabase():
    try:
        from core.supabase_client import get_supabase  # type: ignore
        return get_supabase()
    except Exception:
        return None


def _norm(s: Any) -> str:
    return str(s or "").strip().upper()


def _fmt_num(v: Any, dec: int = 2) -> str:
    try:
        if v is None:
            return "—"
        f = float(v)
        return f"{f:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(v)




def _num(v: Any) -> Optional[float]:
    try:
        if v is None or v == "":
            return None
        if isinstance(v, str):
            s = v.strip().replace(".", "").replace(",", ".")
            if s == "":
                return None
            return float(s)
        return float(v)
    except Exception:
        return None

def _fmt_pct(v: Any, dec: int = 1) -> str:
    try:
        if v is None:
            return "—"
        return f"{float(v):.{dec}f}%"
    except Exception:
        return "—"


def _formula_box(text: str) -> None:
    st.markdown(
        f"""<div style="margin:0.45rem 0 0.9rem 0;padding:0.8rem 1rem;border-left:4px solid #2563eb;background:#f8fafc;border-radius:0.4rem;font-size:1.08rem;font-weight:700;line-height:1.5;">👉 {text}</div>""",
        unsafe_allow_html=True,
    )


def _pct_rule(v: Any) -> Optional[float]:
    try:
        if v is None or v == "":
            return None
        f = float(v)
        return f * 100 if 0 <= f <= 1 else f
    except Exception:
        return None


def _sigla_nome(sigla: str) -> str:
    s = _norm(sigla)
    mapa = {
        "A": "Adequado",
        "I": "Inadequado",
        "AP": "Adequado (pequeno porte)",
        "AM": "Adequado (médio porte)",
        "AP/AM": "Depende do porte (pequeno/médio)",
        "PE": "Projeto especial",
    }
    return mapa.get(s, "")


def _zone_candidates(z: str) -> List[str]:
    z0 = _norm(z)
    cands = [z0]
    if " " in z0:
        cands.append(z0.replace(" ", ""))
    else:
        import re
        z_sp = re.sub(r"(\D)(\d)", r"\1 \2", z0)
        if z_sp != z0:
            cands.append(z_sp)
    cands.append(z0.replace("-", " "))
    out: List[str] = []
    for c in cands:
        c = c.strip().upper()
        if c and c not in out:
            out.append(c)
    return out


def _via_tipo_norm(v: Any) -> Optional[str]:
    s = str(v or "").strip().lower()
    if not s:
        return None
    if "arterial" in s and "pais" in s:
        return "ARTERIAL_PAISAGISTICA"
    if "coletora" in s and "pais" in s:
        return "COLETORA_PAISAGISTICA"
    if "arterial" in s:
        return "ARTERIAL"
    if "coletora" in s:
        return "COLETORA"
    if "pais" in s:
        return "PAISAGISTICA"
    if "troncal" in s or "rodovia federal" in s or "br-" in s or s.startswith("br "):
        return "TRONCAL"
    if "regional" in s or "rodovia estadual" in s or "ce-" in s or s.startswith("ce "):
        return "REGIONAL"
    return None


def _is_zeia_zone(zona: Any) -> bool:
    z = _norm(zona)
    z_key = z.replace("-", "").replace("/", "").replace(" ", "")
    return z_key in {"ZEIAAPP", "ZEIA1", "ZEIA2", "ZEIA3"}


def _summarize_adequabilidade(*, zone_class: str | None, via_norm: str | None, via_class: str | None) -> tuple[str, str, str]:
    z = _norm(zone_class)
    v = _norm(via_class)

    # Quando a via NÃO é arterial/coletora/paisagística correspondente,
    # não há sobreposição pela via. Prevalece a leitura da zona.
    if not via_norm:
        if z == "I":
            return (
                "❌",
                "NÃO PERMITE",
                "A zona indicou I — Inadequado. Como a via identificada não se enquadra nas categorias arterial ou coletora previstas para sobreposição da adequabilidade viária, prevalece a regra da zona."
            )

        if z == "AP":
            return (
                "✅",
                "PERMITE SOMENTE PEQUENO PORTE",
                "O uso é admitido nesta zona apenas como pequeno porte. A análise ainda deve respeitar a Taxa de Ocupação, a Taxa de Permeabilidade, o Índice de Aproveitamento, os recuos, a altura máxima e as demais regras urbanísticas aplicáveis."
            )

        if z == "AP/AM":
            return (
                "✅",
                "PERMITE PEQUENO OU MÉDIO PORTE",
                "O uso é admitido nesta zona nos portes pequeno ou médio. A análise ainda deve respeitar a Taxa de Ocupação, a Taxa de Permeabilidade, o Índice de Aproveitamento, os recuos, a altura máxima e as demais regras urbanísticas aplicáveis."
            )

        if z == "PE":
            return (
                "⚠️",
                "PROJETO ESPECIAL",
                "A zona indicou PE — Projeto Especial. Pode exigir análise específica, condições adicionais ou manifestação do órgão competente no licenciamento."
            )

        if z == "A":
            return (
                "✅",
                "PERMITE",
                "A zona permite o uso, observados Taxa de Ocupação, Taxa de Permeabilidade, Índice de Aproveitamento, recuos, altura máxima e demais regras urbanísticas aplicáveis."
            )

        return (
            "⚠️",
            "SEM DADO",
            "Não foi possível determinar o resultado por zona."
        )

    # Quando a via É arterial/coletora, paisagística ou não,
    # a classificação viária pode se sobrepor à leitura da zona.
    # Via troncal/regional não aparece literalmente no Art. 99, mas é tratada
    # como leitura favorável pela hierarquia/função rodoviária, com ressalva
    # obrigatória sobre anuência do órgão rodoviário competente.
    if via_norm == "TRONCAL":
        return (
            "✅",
            "PERMITE PELA VIA",
            "**Análise pela via:** como o terreno tem frente para uma via troncal, a viabilidade pode ser analisada de forma mais ampla. "
            "Por isso, a viabilidade não fica limitada apenas à classificação indicada pela zona.\n\n"
            "**Limites urbanísticos:** mesmo com leitura favorável pela via, o projeto ainda precisa respeitar os limites urbanísticos do terreno, "
            "como Taxa de Ocupação, Taxa de Permeabilidade, Índice de Aproveitamento, recuos e altura máxima.\n\n"
            "**Atenção — rodovia federal/BR:** o projeto pode depender também de análise/autorização do DNIT, especialmente para acesso de veículos, "
            "entrada e saída do imóvel, intervenção no acostamento, calçada, canteiro ou faixa de domínio, salvo se o trecho estiver formalmente sob responsabilidade municipal."
        )

    if via_norm == "REGIONAL":
        return (
            "✅",
            "PERMITE PELA VIA",
            "**Análise pela via:** como o terreno tem frente para uma via regional, a viabilidade pode ser analisada de forma mais ampla. "
            "Por isso, a viabilidade não fica limitada apenas à classificação indicada pela zona.\n\n"
            "**Limites urbanísticos:** mesmo com leitura favorável pela via, o projeto ainda precisa respeitar os limites urbanísticos do terreno, "
            "como Taxa de Ocupação, Taxa de Permeabilidade, Índice de Aproveitamento, recuos e altura máxima.\n\n"
            "**Atenção — rodovia estadual/CE:** o projeto pode depender também de análise/autorização da SOP/CE, especialmente para acesso de veículos, "
            "entrada e saída do imóvel, intervenção no acostamento, calçada, canteiro ou faixa de domínio, salvo se o trecho estiver formalmente sob responsabilidade municipal."
        )

    if v == "I":
        return (
            "❌",
            "NÃO PERMITE",
            "A classificação viária indicou I — Inadequado. Mesmo que a zona permita, a leitura pela via não admite o uso."
        )

    if v == "A":
        if z == "A":
            return (
                "✅",
                "PERMITE PELA ZONA E PELA VIA",
                "**Análise pela zona e pela via:** o uso pretendido é permitido pela classificação da zona e também pela classificação da via de acesso. "
                "Nesse caso, a leitura é favorável pelos dois critérios.\n\n"
                "**Limites urbanísticos:** mesmo com leitura favorável pela zona e pela via, o projeto ainda precisa respeitar os limites urbanísticos do terreno, "
                "como Taxa de Ocupação, Taxa de Permeabilidade, Índice de Aproveitamento, recuos e altura máxima.\n\n"
                "**Base da leitura:** a zona permite o uso e a via também possui classificação favorável, mantendo a conclusão positiva da análise."
            )

        return (
            "✅",
            "PERMITE PELA VIA",
            "**Análise pela via:** a zona, isoladamente, não indicou permissão plena para o uso pretendido. Porém, a classificação da via permite que a viabilidade seja analisada de forma mais ampla. "
            "Por isso, neste caso, a leitura favorável decorre da via, e a viabilidade não fica limitada apenas à classificação indicada pela zona.\n\n"
            "**Limites urbanísticos:** mesmo com leitura favorável pela via, o projeto ainda precisa respeitar os limites urbanísticos do terreno, "
            "como Taxa de Ocupação, Taxa de Permeabilidade, Índice de Aproveitamento, recuos e altura máxima.\n\n"
            "**Base da leitura:** essa interpretação decorre da regra de sobreposição da adequabilidade pela via prevista no Art. 99 da LC 91/2023."
        )

    if v == "AP":
        return (
            "✅",
            "PERMITE PELA VIA SOMENTE PEQUENO PORTE",
            "A classificação viária indicou AP — Adequado Pequeno Porte. Como o imóvel possui frente para via arterial ou coletora, paisagística ou não, a adequabilidade pela via pode se sobrepor à leitura da zona, limitada ao pequeno porte. Ainda devem ser respeitados os parâmetros urbanísticos da zona."
        )

    if v == "AP/AM":
        return (
            "✅",
            "PERMITE PELA VIA PEQUENO OU MÉDIO PORTE",
            "A classificação viária indicou AP/AM — Adequado Pequeno ou Médio Porte. Como o imóvel possui frente para via arterial ou coletora, paisagística ou não, a adequabilidade pela via pode se sobrepor à leitura da zona, limitada aos portes pequeno e médio. Ainda devem ser respeitados os parâmetros urbanísticos da zona."
        )

    if v == "PE":
        return (
            "⚠️",
            "PROJETO ESPECIAL PELA VIA",
            "A classificação viária indicou PE — Projeto Especial. Mesmo havendo possibilidade pela via, o caso pode exigir análise específica, condições adicionais ou manifestação do órgão competente no licenciamento."
        )

    # Fallback: se a via deveria ser considerada, mas não veio classificação viária,
    # volta para a leitura da zona.
    if z == "I":
        return (
            "❌",
            "NÃO PERMITE",
            "A zona indicou I — Inadequado, e não foi localizada classificação viária favorável suficiente para sobrepor essa restrição."
        )

    if z == "AP":
        return (
            "✅",
            "PERMITE SOMENTE PEQUENO PORTE",
            "O uso é admitido nesta zona apenas como pequeno porte. A análise ainda deve respeitar a Taxa de Ocupação, a Taxa de Permeabilidade, o Índice de Aproveitamento, os recuos, a altura máxima e as demais regras urbanísticas aplicáveis."
        )

    if z == "AP/AM":
        return (
            "✅",
            "PERMITE PEQUENO OU MÉDIO PORTE",
            "O uso é admitido nesta zona nos portes pequeno ou médio. A análise ainda deve respeitar a Taxa de Ocupação, a Taxa de Permeabilidade, o Índice de Aproveitamento, os recuos, a altura máxima e as demais regras urbanísticas aplicáveis."
        )

    if z == "PE":
        return (
            "⚠️",
            "PROJETO ESPECIAL",
            "A zona indicou PE — Projeto Especial. Pode exigir análise específica, condições adicionais ou manifestação do órgão competente no licenciamento."
        )

    return (
        "✅",
        "PERMITE",
        "Zona e/ou tipo de via permitem o uso, observados Taxa de Ocupação, Taxa de Permeabilidade, Índice de Aproveitamento, recuos, altura máxima e demais regras aplicáveis."
    )



# Fallback controlado para a leitura residencial do Item 2.
# Motivo: em alguns ambientes, a tabela de adequabilidade por zona pode não retornar
# a classificação da zona simples, mesmo quando a própria legislação/tabela oficial
# permite o uso residencial. Sem esse apoio, o relatório exibe apenas "PERMITE PELA VIA"
# mesmo quando zona e via são favoráveis.
def _fallback_zone_class_residencial(zone_sigla: str | None) -> str | None:
    z = str(zone_sigla or "").strip().upper()
    z = z.replace("—", "-").replace("_", "").replace("/", "").replace(" ", "")
    if not z:
        return None

    # Zonas/subzonas do MVP residencial que são favoráveis pela zona.
    # Não inclui comércio/serviços e não altera regras futuras desses usos.
    allow_a_prefixes = (
        "ZEIP",  # ZEIP_1 a ZEIP_9 chegam muitas vezes como zone_sigla=ZEIP + subzona/setor.
        "ZCR",
        "ZOP",
        "ZAP",
        "ZAM",
        "ZPP",   # ZPP1, ZPP2 e ZPP3.
    )
    allow_ap_prefixes = (
        "ZEIS1",
        "ZEIS2",
        "ZEIS3",
    )
    deny_i_prefixes = (
        "ZEPE",  # ZEPE1 e ZEPE2 não devem virar "zona e via" para residencial.
        "ZEIA",  # ZEIA_APP, ZEIA1, ZEIA2 e ZEIA3 mantêm leitura especial/restritiva pela zona.
        "ZRO",
    )

    for prefix in allow_a_prefixes:
        if z.startswith(prefix):
            return "A"
    for prefix in allow_ap_prefixes:
        if z.startswith(prefix):
            return "AP"
    for prefix in deny_i_prefixes:
        if z.startswith(prefix):
            return "I"
    return None

def _fetch_adequabilidade(*, zone_sigla: str, via_tipo_texto: Optional[str], use_type_code: str) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
    sb = _get_supabase()
    debug: Dict[str, Any] = {
        "zone_sigla_in": zone_sigla,
        "zone_candidates": [],
        "use_type_code": use_type_code,
        "via_tipo_in": via_tipo_texto,
        "via_tipo_norm": None,
    }
    if sb is None:
        debug["error"] = "supabase_client_not_available"
        return None, None, debug

    zona = _norm(zone_sigla)
    use_code = _norm(use_type_code)
    via_norm = _via_tipo_norm(via_tipo_texto)
    debug["via_tipo_norm"] = via_norm

    zone_class = None
    via_class = None
    try:
        cands = _zone_candidates(zona)
        debug["zone_candidates"] = cands
        res = (
            sb.table("adequab_zonas_sede")
            .select("zone_sigla,classificacao")
            .eq("use_type_code", use_code)
            .in_("zone_sigla", cands)
            .limit(1)
            .execute()
        )
        data = getattr(res, "data", None) or []
        if data:
            zone_class = (data[0].get("classificacao") or "").strip()
            debug["zone_hit"] = data[0].get("zone_sigla")
    except Exception as e:
        debug["zone_error"] = str(e)

    # Correção do Item 2 para uso residencial:
    # se a zona oficial residencial é reconhecida como favorável/restritiva,
    # garantimos que a leitura textual não dependa apenas de a tabela de
    # adequabilidade por zona ter retornado uma linha. Isso corrige o caso
    # ZAM/ZAP/ZCR/ZOP + via A, que deve aparecer como
    # "PERMITE PELA ZONA E PELA VIA".
    if use_code.startswith("RES_"):
        fallback_zone_class = _fallback_zone_class_residencial(zona)
        if fallback_zone_class and _norm(zone_class) != fallback_zone_class:
            debug["zone_fallback_previous_class"] = zone_class
            zone_class = fallback_zone_class
            debug["zone_fallback"] = "residential_zone_class"
            debug["zone_fallback_class"] = fallback_zone_class

    if via_norm:
        try:
            res2 = (
                sb.table("adequab_vias")
                .select("classificacao")
                .eq("use_type_code", use_code)
                .eq("via_tipo", via_norm)
                .limit(1)
                .execute()
            )
            data2 = getattr(res2, "data", None) or []
            if data2:
                via_class = (data2[0].get("classificacao") or "").strip()
        except Exception as e:
            debug["via_error"] = str(e)

    return zone_class, via_class, debug


def _tipo_multifamiliar_label(multi_tipo: str, use_type_code: str) -> str:
    if multi_tipo in ("R21", "R2.1", "R2_1") or use_type_code.endswith("R21"):
        return "R2.1 — 2 unidades no mesmo lote (justapostas ou sobrepostas)"
    if multi_tipo in ("R22", "R2.2", "R2_2") or use_type_code.endswith("R22"):
        return "R2.2 — condomínio horizontal com via interna"
    if multi_tipo in ("R3", "R03") or use_type_code.endswith("R3"):
        return "R3 — residência multifamiliar vertical"
    return "Residência multifamiliar"


def _render_intro_tipo(multi_tipo: str, use_type_code: str) -> None:
    if multi_tipo in ("R21", "R2.1", "R2_1") or use_type_code.endswith("R21"):
        st.markdown("---\n## 🏘️ O que é o residencial multifamiliar R2.1?")
        st.markdown(
            "O **R2.1 é um multifamiliar, mas tem uma regra especial**. Ele é formado por **2 unidades habitacionais no mesmo lote**, podendo ser:\n\n"
            "- **justapostas** → duas unidades lado a lado;\n"
            "- **sobrepostas** → uma unidade embaixo e outra em cima.\n\n"
            "Mesmo sendo classificado como multifamiliar, a **LC 90/2023** determina que cada unidade seja analisada, em alguns pontos, como uma **residência unifamiliar**.\n\n"
            "Isso significa que cada unidade precisa ter **frente e acesso independente para via pública oficial**, **paredes externas total ou parcialmente comuns**, "
            "aparência de **um único conjunto arquitetônico homogêneo**, **no máximo 2 pavimentos** e ambientes mínimos conforme as regras da residência unifamiliar."
        )
    elif multi_tipo in ("R22", "R2.2", "R2_2") or use_type_code.endswith("R22"):
        st.markdown("---\n## 🏘️ O que é o residencial multifamiliar R2.2?")
        st.markdown(
            "O **R2.2** é a tipologia de **residência multifamiliar horizontal em condomínio horizontal**.\n\n"
            "Isso significa que:\n"
            "- as unidades ficam dentro de um **conjunto residencial**;\n"
            "- o acesso principal acontece por **via interna**;\n"
            "- e a unidade **não abre diretamente para a via pública oficial**.\n\n"
            "👉 **Em resumo:** o **R2.2** é um condomínio horizontal com circulação interna, diferente do **R2.1**, em que cada unidade tem frente direta para a rua."
        )
    elif multi_tipo in ("R3", "R03") or use_type_code.endswith("R3"):
        st.markdown("---\n## 🏢 O que é o residencial multifamiliar R3?")
        st.markdown(
            "O **R3** é a tipologia de **residência multifamiliar vertical**.\n\n"
            "Isso significa que:\n"
            "- as unidades ficam organizadas em um **edifício residencial**;\n"
            "- o conjunto funciona como um **prédio multifamiliar**;\n"
            "- e a análise precisa considerar não só as unidades, mas também a estrutura comum da edificação.\n\n"
            "👉 **Em resumo:** o **R3** é o multifamiliar vertical, diferente do **R2.1** e do **R2.2**, que são multifamiliares horizontais."
        )


def _render_dicas_valiosas(multi_tipo: str, use_type_code: str) -> None:

    if multi_tipo in ("R21", "R2.1", "R2_1") or use_type_code.endswith("R21"):
        sections = [
            ("R2.1 — regra especial", [
                "pode ter **no máximo 2 pavimentos**;",
                "cada unidade deve ter **frente e acesso independente para via pública oficial**;",
                "as paredes externas devem ser **total ou parcialmente comuns**;",
                "o conjunto deve ter aparência de **unidade arquitetônica homogênea**;",
                "cada unidade deve atender os mínimos do **Anexo II**, como na residência unifamiliar;",
                "quando aplicável, pode ser considerada a flexibilidade do **art. 112** para recuos de frente e laterais, mantendo a **Taxa de Ocupação (TO)** máxima e a **Taxa de Permeabilidade (TP)** mínima da zona;",
                "quando a testada ficar abaixo da referência usual de **8,00 m** fora de ZEIS, o caso exige análise no licenciamento e comprovação documental da situação do lote.",
            ], "o **R2.1** é multifamiliar na tipologia, mas em alguns parâmetros é analisado com lógica semelhante à residência unifamiliar. A área máxima do térreo não dobra: ela continua limitada pela **Taxa de Ocupação (TO)**, pela **Taxa de Permeabilidade (TP)** e pelo que cabe fisicamente no lote."),
            ("IA e área computável", [
                "**Art. 110 da LC 91:** a área computável para o Índice de Aproveitamento (**IA**) é calculada pela soma das áreas das unidades autônomas.",
                "A lei também considera como **não computáveis**, entre outros:",
                "- obras complementares;",
                "- garagens sob pilotis e subsolos usados para estacionamento;",
                "- halls, escadas, elevadores e salões de festas em multifamiliar;",
                "- áreas comerciais e de serviços no térreo de uso misto.",
            ], "mesmo no **R2.1**, o **IA da zona continua importando**, e a forma de calcular a área computável também precisa ser observada."),
            ("Subsolo", [
                "Quando a zona permitir subsolo, ele deve respeitar:",
                "- a **Taxa de Ocupação do subsolo**;",
                "- a **Taxa de Permeabilidade**;",
                "- os **recuos mínimos da zona**;",
                "E, se houver subsolo, deve haver **recuo mínimo de 1,50 m em todas as divisas**.",
            ], "essa verificação só passa a ser relevante se o estudo realmente considerar subsolo no lote."),
        ]
    elif multi_tipo in ("R22", "R2.2", "R2_2") or use_type_code.endswith("R22"):
        sections = [
            ("R2.2 — condomínio horizontal", [
                "funciona como **condomínio horizontal**, com **via interna**;",
                "a unidade **não pode ter acesso direto para a via pública oficial**;",
                "é preciso verificar se o lote está dentro da **quadra máxima da zona**, porque essa exigência aparece expressamente para **R2.2** e **R3**;",
                "exige estrutura de condomínio, com organização interna e circulação própria.",
            ], "o **R2.2** não funciona como “casas independentes voltadas para a rua”, e sim como um conjunto residencial horizontal com acesso e circulação internos."),
            ("Exigências específicas do condomínio horizontal", [
                "O **art. 168 da LC 90** exige, entre outros pontos:",
                "- abertura mínima de acesso: 4,00 m;",
                "- **altura livre mínima no acesso:** 4,50 m;",
                "- **vias internas com 6,00 m**, conforme norma do Corpo de Bombeiros;",
                "- **acessibilidade** *(como rotas acessíveis e uso comum adequado)*;",
                "- **circulação interna** *(como deslocamento entre unidades, acessos e áreas comuns)*;",
                "- **rampas em áreas comuns** *(quando existirem desníveis no conjunto)*;",
                "- **exigências de uso comum** *(como áreas coletivas, apoio e funcionamento do condomínio)*;",
                "- **instalações para funcionários / DML**;",
                "- **25% do muro frontal em gradil ou material vazado**;",
                "- **local para resíduos no alinhamento com abertura para o logradouro**;",
                "- **regime de condomínio ou único proprietário**.",
            ], "no R2.2, o projeto precisa pensar não só nas unidades, mas também na operação e na infraestrutura do condomínio."),
            ("Área recreativa", [
                "Se o empreendimento tiver **mais de 10 unidades**, deve prever **área recreativa mínima de 5% da área total do terreno**."
            ], "conjuntos maiores precisam reservar espaço de lazer e convivência."),
            ("IA e área computável", [
                "**Art. 110 da LC 91:** a área computável para o Índice de Aproveitamento (**IA**) é calculada pela soma das áreas das unidades autônomas.",
                "A lei também considera como **não computáveis**, entre outros:",
                "- obras complementares;",
                "- garagens sob pilotis e subsolos para estacionamento;",
                "- halls, escadas, elevadores e salões de festas;",
                "- áreas comerciais e de serviços no térreo em uso misto, com acessos individualizados.",
            ], "no **R2.2**, a conta do IA precisa observar não só as unidades, mas também o que entra ou não entra como área computável."),
            ("Subsolo", [
                "Se a zona permitir subsolo, ele deve respeitar:",
                "- a **TO do subsolo**;",
                "- a **TP**;",
                "- os **recuos mínimos da zona**;",
                "E, se houver subsolo, deve haver **recuo mínimo de 1,50 m em todas as divisas**.",
            ], "essa regra passa a ser relevante quando o estudo considerar subsolo no condomínio."),
            ("EIV", [
                "Para uso residencial multifamiliar:",
                "- será exigido **EIV** quando houver **mais de 100 unidades habitacionais**.",
            ], "essa exigência pode atingir o **R2.2** dependendo do porte do conjunto."),
        ]
    else:
        sections = [
            ("R3 — multifamiliar vertical", [
                "corresponde à **residência multifamiliar vertical**, organizada em edifício;",
                "é preciso verificar se o lote está dentro da **quadra máxima da zona**, porque essa exigência aparece expressamente para **R2.2** e **R3**;",
                "o estudo deve considerar não só as unidades, mas também a estrutura comum do edifício;",
                "o prédio exige organização condominial ou único proprietário.",
            ], "o **R3** não é só “um lote com várias unidades”, mas um edifício com exigências próprias de funcionamento, circulação e apoio."),
            ("Exigências específicas do multifamiliar vertical", [
                "O **art. 170 da LC 90** exige, entre outros pontos:",
                "- acesso ao estacionamento conforme os dimensionamentos e norma do Corpo de Bombeiros;",
                "- **área recreativa mínima de 5% da área total construída das unidades**;",
                "- **acessibilidade** *(como rotas acessíveis e uso comum adequado)*;",
                "- **circulação** *(como deslocamento vertical e horizontal dentro do edifício)*;",
                "- **acesso ao estacionamento** *(incluindo entrada, saída e manobra)*;",
                "- **instalações para funcionários / DML**;",
                "- **50% do muro frontal em gradil ou material vazado**;",
                "- **local para resíduos no alinhamento com abertura para o logradouro**;",
                "- **regime de condomínio ou único proprietário**;",
                "- se houver **mais de 30 unidades**, espaço de entrega/recepção com no mínimo **5 m²** no alinhamento do lote.",
            ], "no **R3**, a análise precisa olhar o edifício como conjunto, e não só as unidades residenciais."),
            ("Área recreativa", [
                "No multifamiliar vertical, a área recreativa mínima é de:",
                "- **5% da área total construída das unidades**",
            ], "no prédio residencial, a área recreativa é calculada de forma diferente do condomínio horizontal."),
            ("IA e área computável", [
                "**Art. 110 da LC 91:** a área computável para o Índice de Aproveitamento (**IA**) é a soma das áreas das unidades autônomas.",
                "A lei também considera como **não computáveis**, entre outros:",
                "- obras complementares;",
                "- garagens sob pilotis e subsolos para estacionamento;",
                "- áreas comuns como halls, escadas, elevadores e salões de festas em multifamiliar;",
                "- áreas comerciais e de serviços no térreo em uso misto, com acessos individualizados.",
            ], "no **R3**, esse ponto é muito importante porque o edifício costuma ter várias áreas comuns, e nem tudo entra na conta do IA."),
            ("Subsolo", [
                "Se a zona permitir subsolo:",
                "- deve respeitar a **TO do subsolo**;",
                "- a **TP**;",
                "- os **recuos mínimos da zona**;",
                "- e, havendo subsolo, deve existir **recuo mínimo de 1,50 m em todas as divisas**.",
            ], "no **R3**, essa regra é muito relevante, especialmente quando o projeto depender de garagem em subsolo."),
            ("EIV", [
                "Para uso residencial multifamiliar:",
                "- será exigido **EIV** quando houver **mais de 100 unidades habitacionais**.",
            ], "essa é uma regra que pode atingir o **R3** com mais frequência do que o **R2.1**, por causa do porte possível do edifício."),
        ]

    for title, bullets, practical in sections:
        st.markdown(f"#### {title}")
        for line in bullets:
            st.markdown(line)
        st.markdown(f"👉 **Na prática:** {practical}")

    st.markdown("#### Passeios (calçadas)")
    st.markdown(
        "Não há, na legislação municipal, uma medida única e fixa para a largura dos passeios. "
        "Quando existir, deve-se adotar o padrão definido no projeto aprovado do loteamento e/ou nas diretrizes urbanísticas da via; "
        "na ausência dessa previsão, utiliza-se como referência o passeio já implantado no logradouro."
    )

    st.markdown("#### Piscina, caixa d’água, cisterna e tanques")
    st.markdown("**Atenção:** para a Taxa de Ocupação (TO), a piscina não é contada como área construída do lote.")
    st.markdown(
        "**Art. 144.** As piscinas, espelhos d’água, caixas d’água, cisternas e tanques deverão observar um afastamento mínimo de **0,50 m** "
        "de todas as divisas do terreno e devem ser computados como área impermeável para o cálculo da Taxa de Permeabilidade."
    )
    st.markdown(
        "👉 **Na prática:** além de respeitar esse afastamento mínimo de **50 cm**, esses elementos também entram no cálculo da **TP** como área impermeável."
    )


def _render_alvara_section() -> None:
    st.markdown(
        "Após a finalização dos projetos, será necessário dar entrada na documentação junto à **Prefeitura** para obter o **alvará de construção**.\n\n"
        "De forma geral, esse processo pode seguir por **duas vias**:\n\n"
        "- **Alvará de Construção Simplificado** → voltado para casos mais simples e de menor porte;\n"
        "- **Alvará de Construção (Obra Nova)** → usado quando a obra exige análise técnica mais completa e documentação complementar.\n\n"
        "Abaixo está um resumo dos dois caminhos e um checklist básico dos itens que normalmente precisam ser providenciados."
    )

    st.markdown("#### 📄 Alvará de Construção Simplificado")
    st.markdown(
        "O **Alvará de Construção Simplificado** é uma forma mais rápida de licenciamento, voltada para casos mais simples. "
        "Ele costuma ser usado para **residência unifamiliar** e para **comércio/serviços de pequeno porte**, com área construída de até **250,00 m²**.\n\n"
        "A lógica desse alvará é mais enxuta e autodeclaratória, mas isso não elimina a necessidade de apresentar os documentos corretos "
        "e atender às exigências urbanísticas e técnicas do Município."
    )
    st.markdown("**✅ Checklist — documentos e itens principais**")
    for item in [
        "Documento de identidade do requerente ou representante legal",
        "CPF ou CNPJ",
        "Matrícula atualizada do imóvel ou documento equivalente",
        "Certidão negativa de IPTU",
        "Parecer favorável de Adequabilidade Locacional",
        "Tabela com índices urbanísticos e áreas da edificação",
        "Projeto arquitetônico em arquivo digital",
        "ART/RRT do responsável técnico",
        "Termo de responsabilidade do responsável técnico",
        "Termo de responsabilidade do proprietário",
        "Isenção da licença ambiental",
    ]:
        st.markdown(f"- [ ] {item}")
    st.markdown("**📌 Atenção**")
    for item in [
        "Confirmar se o caso realmente se enquadra como simplificado",
        "Conferir se a área construída está dentro do limite permitido",
        "Protocolar o pedido com antecedência mínima indicada pelo procedimento",
        "Verificar se todos os arquivos digitais estão prontos e legíveis",
    ]:
        st.markdown(f"- [ ] {item}")

    st.markdown("#### 🏗️ Alvará de Construção (Obra Nova)")
    st.markdown(
        "O **Alvará de Construção (Obra Nova)** é o caminho regular de licenciamento para obras novas que exigem análise técnica completa da Prefeitura. "
        "Ele é mais detalhado e costuma ser necessário em casos que não se enquadram no procedimento simplificado ou que exigem documentação complementar.\n\n"
        "Esse tipo de alvará pede uma conferência mais ampla do projeto, incluindo aspectos urbanísticos, arquitetônicos, hidrossanitários, ambientais "
        "e, em alguns casos, exigências de outros órgãos."
    )
    st.markdown("**✅ Checklist — documentos principais**")
    for item in [
        "Requerimento único",
        "Documento de identidade do requerente ou representante legal",
        "CPF ou CNPJ",
        "Matrícula atualizada do imóvel",
        "Autorização do proprietário, quando necessária",
        "BCI",
        "ART/RRT com comprovante de pagamento",
        "Projeto arquitetônico assinado",
        "Projeto hidrossanitário",
        "Memorial de cálculo e drenagem pluvial",
        "Declaração do SAAE sobre rede de esgoto, quando necessária",
    ]:
        st.markdown(f"- [ ] {item}")
    st.markdown("**✅ Checklist — documentos adicionais que podem ser exigidos**")
    for item in [
        "Aprovação do Corpo de Bombeiros",
        "Aprovação do IPHAN, quando o imóvel estiver em ZEIP",
        "Licenciamento ambiental ou termo de isenção",
        "PGRSCC",
        "Autorização do COMAR, quando aplicável",
        "Aprovação do DNIT ou SOP, quando houver acesso por rodovia",
        "EIV, quando exigido pela legislação",
    ]:
        st.markdown(f"- [ ] {item}")
    st.markdown("**📌 Atenção**")
    for item in [
        "Confirmar se o caso realmente exige alvará regular de obra nova",
        "Conferir se há exigência de documentos complementares por localização ou tipologia",
        "Verificar se o imóvel está em área com proteção especial",
        "Conferir se o projeto atende às exigências técnicas antes do protocolo",
    ]:
        st.markdown(f"- [ ] {item}")




def build_context(*, calc: Dict[str, Any], rule: Optional[Dict[str, Any]] = None, fetch_adequabilidade_fn=None, is_irregular: Any = None) -> Dict[str, Any]:
    """Monta e devolve o contexto compartilhado do relatório multifamiliar."""
    multi_tipo = _norm(calc.get("multi_tipo"))
    use_type_code = _norm(calc.get("use_type_code"))
    zona = _norm(calc.get("zone") or calc.get("zone_sigla"))
    via = calc.get("via_nome") or calc.get("street_name") or "—"
    via_tipo_txt = calc.get("via_tipo") or calc.get("via_type") or "via local"
    subzona = calc.get("subzone_code") or (rule or {}).get("subzone_code") or "PADRAO"
    zone_label = calc.get("zone") or calc.get("zone_label_raw") or zona
    lot_area = calc.get("lot_area_m2")
    is_irregular_lot = is_irregular_context({"is_irregular": is_irregular}, calc) or bool(
        st.session_state.get("lot_is_irregular")
        or st.session_state.get("lot_irregular")
    )
    if is_irregular_lot:
        lot_front = 0
        lot_depth = 0
        is_corner = False
        tipo_lote = "Terreno irregular"
    else:
        lot_front = calc.get("lot_front_m") or calc.get("front_m") or 0
        lot_depth = calc.get("lot_depth_m") or calc.get("depth_m") or 0
        is_corner = bool(st.session_state.get("lot_is_corner") or calc.get("lot_is_corner") or False)
        tipo_lote = "Esquina" if is_corner else "Meio de quadra"
    uso_label = _tipo_multifamiliar_label(multi_tipo, use_type_code)

    try:
        lot_area_f = float(lot_area) if lot_area not in (None, "", "-") else None
    except Exception:
        lot_area_f = None

    fetch_fn = fetch_adequabilidade_fn or _fetch_adequabilidade
    zone_class, via_class, dbg = fetch_fn(
        zone_sigla=zona,
        via_tipo_texto=via_tipo_txt,
        use_type_code=use_type_code,
    )
    via_norm = _via_tipo_norm(via_tipo_txt)
    icon, status_curto, explicacao = _summarize_adequabilidade(zone_class=zone_class, via_norm=via_norm, via_class=via_class)

    if _is_zeia_zone(zona) and status_curto == "PERMITE PELA VIA":
        explicacao += (
            "\n\n**Observação ambiental e documental:** como o terreno está em área de interesse ambiental, "
            "a viabilidade final não dispensa análise do órgão municipal competente, verificação das restrições ambientais aplicáveis, "
            "atendimento aos parâmetros urbanísticos da zona e comprovação da regularidade documental do imóvel, "
            "como matrícula, escritura, registro ou outro documento hábil exigido no licenciamento."
        )

    try:
        from core.zone_descriptions import fetch_zone_description
        desc = fetch_zone_description(str(zona or ""), str(subzona or "PADRAO"), str(zone_label or ""))
    except Exception:
        desc = None

    if rule and isinstance(rule, dict) and lot_area_f and lot_area_f > 0:
        to_max_pct = _pct_rule(rule.get("to_max_pct")) or _pct_rule(rule.get("to_max"))
        tp_min_pct = _pct_rule(rule.get("tp_min_pct")) or _pct_rule(rule.get("tp_min"))
        ia_max = rule.get("ia_max")
        ia_min = rule.get("ia_min")
        try:
            ia_max_f = float(ia_max) if ia_max not in (None, "") else None
        except Exception:
            ia_max_f = None

        to_m2 = lot_area_f * (to_max_pct / 100.0) if isinstance(to_max_pct, (int, float)) else None
        tp_m2 = lot_area_f * (tp_min_pct / 100.0) if isinstance(tp_min_pct, (int, float)) else None
        ia_m2 = lot_area_f * ia_max_f if ia_max_f is not None else None

        gabarito = rule.get("gabarito_m") or rule.get("altura_max_m")
        try:
            gabarito_f = float(gabarito) if gabarito not in (None, "") else None
        except Exception:
            gabarito_f = None
        pav_est = max(1, int(math.floor(gabarito_f / 3.0))) if gabarito_f else None

        try:
            rec_fr = float(rule.get("recuo_frontal_m")) if rule.get("recuo_frontal_m") not in (None, "") else None
        except Exception:
            rec_fr = None
        try:
            rec_lat = float(rule.get("recuo_lateral_m")) if rule.get("recuo_lateral_m") not in (None, "") else None
        except Exception:
            rec_lat = None
        try:
            rec_fun = float(rule.get("recuo_fundos_m")) if rule.get("recuo_fundos_m") not in (None, "") else None
        except Exception:
            rec_fun = None

        area_min = rule.get("area_min_lote_m2") or rule.get("area_lote_min_m2") or rule.get("lote_min_area_m2")
        area_max = rule.get("area_max_lote_m2") or rule.get("lote_max_area_m2")
        testada_min = rule.get("testada_min_m") or rule.get("testada_min_meio_m") or rule.get("testada_min_esquina_m")
        testada_max = rule.get("testada_max_m")

        W = float(lot_front or 0) if lot_front not in (None, "") else 0.0
        D = float(lot_depth or 0) if lot_depth not in (None, "") else 0.0
        W_util = None
        D_util = None
        A_recuos = None
        if (not is_irregular_lot) and rec_lat is not None and rec_fr is not None and rec_fun is not None and W > 0 and D > 0:
            W_util = W - 2 * rec_lat
            D_util = D - rec_fr - rec_fun
            if W_util > 0 and D_util > 0:
                A_recuos = W_util * D_util

        built_ground = _num(
            st.session_state.get("built_ground_m2")
            or calc.get("built_ground_m2")
            or st.session_state.get("built_ground_input_m2")
            or calc.get("built_ground_input_m2")
        )
        teto_pratico = A_recuos if A_recuos is not None else to_m2
        if to_m2 is not None and teto_pratico is not None:
            teto_pratico = min(to_m2, teto_pratico)
        elif teto_pratico is None:
            teto_pratico = to_m2
        is_r21 = multi_tipo in ("R21", "R2.1", "R2_1") or use_type_code.endswith("R21")
        is_zeip9 = str(subzona or "").strip().upper().replace("-", "_") in ("ZEIP_9", "ZEIP9")
        # A ressalva de testada inferior a 8 m para R2.1 vale fora de ZEIS.
        # Em ZEIS, a regra específica da zona prevalece e não deve gerar este alerta.
        r21_testada_baixa = bool(is_r21 and W > 0 and W < 8.0 and not _profile_is_zeis(zona, subzona))
        teto_relatorio = to_m2 if (is_r21 and to_m2 is not None) else teto_pratico
        a_adotada = min(built_ground, teto_relatorio) if (built_ground is not None and built_ground > 0 and teto_relatorio is not None) else (built_ground if (built_ground is not None and built_ground > 0) else None)
        to_utilizada_pct = ((a_adotada / lot_area_f) * 100.0) if (a_adotada is not None and lot_area_f not in (None, 0)) else None
        ia_consumido_terreo = (a_adotada / lot_area_f) if (a_adotada is not None and lot_area_f not in (None, 0)) else None
        area_livre_projeto = (lot_area_f - a_adotada) if (a_adotada is not None and lot_area_f is not None) else None
        area_impermavel_pos_tp = (area_livre_projeto - tp_m2) if (area_livre_projeto is not None and tp_m2 is not None) else None
        ia_saldo = (ia_m2 - a_adotada) if (ia_m2 is not None and a_adotada is not None) else None
    else:
        to_max_pct = tp_min_pct = ia_max = ia_min = to_m2 = tp_m2 = ia_m2 = gabarito_f = pav_est = None
        rec_fr = rec_lat = rec_fun = area_min = area_max = testada_min = testada_max = None
        W_util = D_util = A_recuos = None
        built_ground = teto_pratico = teto_relatorio = a_adotada = to_utilizada_pct = ia_consumido_terreo = area_livre_projeto = area_impermavel_pos_tp = ia_saldo = None
        is_r21 = False
        is_zeip9 = str(subzona or "").strip().upper().replace("-", "_") in ("ZEIP_9", "ZEIP9")
        r21_testada_baixa = False

    policy = apply_zone_result_policy(
        zona=zona,
        subzona=subzona,
        via_norm=via_norm,
        via_class=via_class,
        zone_class=zone_class,
        status=status_curto,
        icon=icon,
        explanation=explicacao,
        use_type_code=use_type_code,
    )
    icon, status_curto, explicacao = policy.icon, policy.status, policy.explanation

    if r21_testada_baixa and str(status_curto or "").strip().upper() != "NÃO PERMITE":
        icon = "⚠️"
        status_curto = "PERMITE COM RESSALVA — R2.1"

    ctx_out = {
        "calc": calc,
        "rule": rule or {},
        "multi_tipo": multi_tipo,
        "use_type_code": use_type_code,
        "zona": zona,
        "via": via,
        "via_tipo_txt": via_tipo_txt,
        "subzona": subzona,
        "zone_label": zone_label,
        "lot_area_f": lot_area_f,
        "lot_front": lot_front,
        "lot_depth": lot_depth,
        "is_corner": is_corner,
        "is_irregular": is_irregular_lot,
        "tipo_lote": tipo_lote,
        "uso_label": uso_label,
        "zone_class": zone_class,
        "via_class": via_class,
        "dbg": dbg,
        "via_norm": via_norm,
        "icon": icon,
        "status_curto": status_curto,
        "explicacao": explicacao,
        "desc": desc,
        "to_max_pct": to_max_pct,
        "tp_min_pct": tp_min_pct,
        "ia_max": ia_max,
        "ia_min": ia_min,
        "to_m2": to_m2,
        "tp_m2": tp_m2,
        "ia_m2": ia_m2,
        "gabarito_f": gabarito_f,
        "pav_est": pav_est,
        "rec_fr": rec_fr,
        "rec_lat": rec_lat,
        "rec_fun": rec_fun,
        "area_min": area_min,
        "area_max": area_max,
        "testada_min": testada_min,
        "testada_max": testada_max,
        "W_util": W_util,
        "D_util": D_util,
        "A_recuos": A_recuos,
        "built_ground": built_ground,
        "teto_pratico": teto_pratico,
        "teto_relatorio": teto_relatorio,
        "a_adotada": a_adotada,
        "to_utilizada_pct": to_utilizada_pct,
        "ia_consumido_terreo": ia_consumido_terreo,
        "area_livre_projeto": area_livre_projeto,
        "area_impermavel_pos_tp": area_impermavel_pos_tp,
        "ia_saldo": ia_saldo,
        "is_r21": is_r21,
        "is_zeip9": is_zeip9,
        "r21_testada_baixa": r21_testada_baixa,
    }
    ctx_out["zone_warnings"] = zone_context_warnings(ctx_out)
    return ctx_out


# Aliases de compatibilidade para a arquitetura modular
_md = md
_md_table = md_table
