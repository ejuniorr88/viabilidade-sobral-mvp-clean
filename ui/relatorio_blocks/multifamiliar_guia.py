
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, List

import math
import streamlit as st


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
    return None


def _summarize_adequabilidade(*, zone_class: str | None, via_norm: str | None, via_class: str | None) -> tuple[str, str, str]:
    z = _norm(zone_class)
    v = _norm(via_class)

    if not via_norm:
        if z == "I":
            return ("❌", "NÃO PERMITE", "A zona indicou I (Inadequado / não permitido). Em via local, normalmente vale a regra da zona.")
        if z == "AP/AM":
            return ("⚠️", "DEPENDE DO PORTE", "A zona indicou AP/AM (depende do porte). Em via local, normalmente vale a regra da zona.")
        if z == "PE":
            return ("⚠️", "PROJETO ESPECIAL", "A zona indicou PE (Projeto especial). Pode exigir análise/condições extras no licenciamento.")
        if z in ("A", "AP", "AM"):
            return ("✅", "PERMITE", "A zona permite. Ainda é obrigatório cumprir TO, TP, IA, recuos, altura e as demais regras aplicáveis.")
        return ("⚠️", "SEM DADO", "Não foi possível determinar o resultado por zona.")

    if v == "I":
        return ("❌", "NÃO PERMITE", "O tipo de via indicou I (não permitido), mesmo que a zona permita.")
    if z == "I" and v in ("A", "AP", "AM"):
        return ("⚠️", "POSSÍVEL PELA VIA", "A zona deu I, mas o tipo de via permite. O licenciamento pode considerar o resultado por tipo de via.")
    if z == "I" and v == "AP/AM":
        return ("⚠️", "DEPENDE DO PORTE", "A zona deu I, mas o tipo de via deu AP/AM (depende do porte). Pode depender do licenciamento.")
    if z == "I" and v == "PE":
        return ("⚠️", "PROJETO ESPECIAL", "A zona deu I, mas o tipo de via indica PE (Projeto especial). Pode exigir análise/condições extras.")
    if z == "AP/AM" or v == "AP/AM":
        return ("⚠️", "DEPENDE DO PORTE", "Existe indicação AP/AM (depende do porte). Confira se o empreendimento é pequeno ou médio.")
    if z == "PE" or v == "PE":
        return ("⚠️", "PROJETO ESPECIAL", "Existe indicação PE (Projeto especial). Pode exigir análise/condições extras no licenciamento.")
    return ("✅", "PERMITE", "Zona e/ou tipo de via permitem. Ainda é obrigatório cumprir TO, TP, IA, recuos, altura e as demais regras aplicáveis.")


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
            "É o caso em que existem **2 unidades habitacionais no mesmo lote**, podendo ser:\n\n"
            "- **justapostas** → residências lado a lado (**horizontal**)\n"
            "- **sobrepostas** → uma unidade embaixo e outra em cima\n\n"
            "Cada unidade deve ter **frente e acesso independente para via pública oficial**.\n\n"
            "**R2.1 — 2 unidades no mesmo lote (justapostas ou sobrepostas), com no máximo 2 pavimentos.**"
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
            ("R2.1 justaposto", [
                "pode ter **no máximo 2 pavimentos**;",
                "**fora da ZEIS**, se for **justaposto**, exige **testada mínima de 8,00 m**;",
                "quando a zona permitir, pode usar os parâmetros do **unifamiliar**, respeitando a adequabilidade;",
                "cada unidade deve atender os mínimos do **Anexo II**, como no unifamiliar;",
                "cada unidade deve ter acesso independente para a via pública oficial.",
            ], "quando a zona permitir esse enquadramento, o **R2.1 justaposto** pode seguir a lógica do **unifamiliar** para parâmetros como recuos, TO, TP, IA, altura e testada mínima."),
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


def render_multifamiliar_guia(*, calc: Dict[str, Any], rule: Optional[Dict[str, Any]] = None, **_: Any) -> None:
    from .quadro_tecnico import render_quadro_tecnico
    from .figuras_anexo_v import render_figuras_anexo_v

    multi_tipo = _norm(calc.get("multi_tipo"))
    use_type_code = _norm(calc.get("use_type_code"))
    zona = _norm(calc.get("zone") or calc.get("zone_sigla"))
    via = calc.get("via_nome") or calc.get("street_name") or "—"
    via_tipo_txt = calc.get("via_tipo") or calc.get("via_type") or "via local"
    subzona = calc.get("subzone_code") or (rule or {}).get("subzone_code") or "PADRAO"
    zone_label = calc.get("zone") or calc.get("zone_label_raw") or zona
    lot_area = calc.get("lot_area_m2")
    lot_front = calc.get("lot_front_m") or calc.get("front_m") or 0
    lot_depth = calc.get("lot_depth_m") or calc.get("depth_m") or 0
    is_corner = bool(st.session_state.get("lot_is_corner") or False)
    tipo_lote = "Esquina" if is_corner else "Meio de quadra"
    uso_label = _tipo_multifamiliar_label(multi_tipo, use_type_code)

    try:
        lot_area_f = float(lot_area) if lot_area not in (None, "", "-") else None
    except Exception:
        lot_area_f = None

    zone_class, via_class, dbg = _fetch_adequabilidade(
        zone_sigla=zona,
        via_tipo_texto=via_tipo_txt,
        use_type_code=use_type_code,
    )
    via_norm = _via_tipo_norm(via_tipo_txt)
    icon, status_curto, explicacao = _summarize_adequabilidade(zone_class=zone_class, via_norm=via_norm, via_class=via_class)

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

        area_min = rule.get("area_lote_min_m2") or rule.get("lote_min_area_m2")
        testada_min = rule.get("testada_min_m")

        W = float(lot_front or 0) if lot_front not in (None, "") else 0.0
        D = float(lot_depth or 0) if lot_depth not in (None, "") else 0.0
        W_util = None
        D_util = None
        A_recuos = None
        if rec_lat is not None and rec_fr is not None and rec_fun is not None and W > 0 and D > 0:
            W_util = W - 2 * rec_lat
            D_util = D - rec_fr - rec_fun
            if W_util > 0 and D_util > 0:
                A_recuos = W_util * D_util

        tp_rest_recuos = (lot_area_f - A_recuos) if (lot_area_f is not None and A_recuos is not None) else None
        tp_imperm_recuos = (tp_rest_recuos - tp_m2) if (tp_rest_recuos is not None and tp_m2 is not None) else None
        tp_rest_to = (lot_area_f - to_m2) if (lot_area_f is not None and to_m2 is not None) else None
        tp_imperm_to = (tp_rest_to - tp_m2) if (tp_rest_to is not None and tp_m2 is not None) else None

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
        teto_relatorio = to_m2 if (is_r21 and to_m2 is not None) else teto_pratico
        a_adotada = min(built_ground, teto_relatorio) if (built_ground is not None and built_ground > 0 and teto_relatorio is not None) else (built_ground if (built_ground is not None and built_ground > 0) else None)
        to_utilizada_pct = ((a_adotada / lot_area_f) * 100.0) if (a_adotada is not None and lot_area_f not in (None, 0)) else None
        ia_consumido_terreo = (a_adotada / lot_area_f) if (a_adotada is not None and lot_area_f not in (None, 0)) else None
        area_livre_projeto = (lot_area_f - a_adotada) if (a_adotada is not None and lot_area_f is not None) else None
        area_impermavel_pos_tp = (area_livre_projeto - tp_m2) if (area_livre_projeto is not None and tp_m2 is not None) else None
        ia_saldo = (ia_m2 - a_adotada) if (ia_m2 is not None and a_adotada is not None) else None
    else:
        to_max_pct = tp_min_pct = ia_max = ia_min = to_m2 = tp_m2 = ia_m2 = gabarito_f = pav_est = None
        rec_fr = rec_lat = rec_fun = area_min = testada_min = None
        W_util = D_util = A_recuos = None
        tp_rest_recuos = tp_imperm_recuos = tp_rest_to = tp_imperm_to = None
        built_ground = teto_pratico = teto_relatorio = a_adotada = to_utilizada_pct = ia_consumido_terreo = area_livre_projeto = area_impermavel_pos_tp = ia_saldo = None
        is_r21 = False

    st.markdown("## 🏢 RELATÓRIO URBANÍSTICO")
    st.markdown(
        "Este relatório mostra, de forma simples, se o uso residencial multifamiliar pode ou não ser desenvolvido neste terreno, "
        "com base na zona, na via e nas regras urbanísticas do município.\n\n"
        "A ideia aqui é facilitar a leitura: primeiro explicamos o tipo multifamiliar analisado, depois mostramos onde o terreno está localizado, "
        "verificamos se o uso é viável e, em seguida, apresentamos os principais limites urbanísticos e pontos importantes para iniciar o estudo do projeto.\n\n"
        "**Importante:** este relatório é uma análise inicial. A aprovação final depende da conferência completa no licenciamento."
    )

    _render_intro_tipo(multi_tipo, use_type_code)

    st.markdown("---\n### 📍 1️⃣ Onde está localizado o terreno?")
    st.markdown("Aqui entram:")
    st.markdown(
        f"- **Uso informado:** {uso_label}\n"
        f"- **Área do terreno:** {_fmt_num(lot_area_f)} m²\n"
        f"- **Dimensões:** {_fmt_num(lot_front)} m × {_fmt_num(lot_depth)} m\n"
        f"- **Zona:** {zona or '—'}\n"
        f"- **Subzona / setor:** {subzona}\n"
        f"- **Tipo de lote:** {tipo_lote}\n"
        f"- **Via:** {via}\n"
        f"- **Tipo de via:** {via_tipo_txt or '—'}"
    )
    st.markdown("**Essas informações são a base de toda a leitura do relatório.**")

    st.markdown("---\n### ✅ 2️⃣ O uso residencial multifamiliar é viável neste terreno?")
    st.markdown("**Para o uso residencial multifamiliar, a permissão pode depender principalmente da zona e, em alguns casos, também do tipo da via e do porte do empreendimento.**")
    if not zone_class and not via_class:
        st.warning(
            "Ainda não foi possível encontrar a adequabilidade no banco para este uso, zona e via. "
            "Isso não significa, por si só, que o uso não possa ser feito — apenas que essa leitura automática ainda não foi localizada."
        )
        with st.expander("🔎 Diagnóstico (para conferência)"):
            st.json(dbg)
    else:
        via_line = f"- **Por via:** {via_class} ({_sigla_nome(via_class)})" if via_norm and via_class else f"- **Por via:** {via_tipo_txt or 'via local'}"
        st.markdown(
            f"- **Por zona:** {zone_class or 'não encontrado'}"
            + (f" ({_sigla_nome(zone_class)})" if zone_class else "")
            + "\n"
            + via_line
            + f"\n- **Resumo final:** {icon} **{status_curto}**"
        )
        if status_curto == "PERMITE":
            st.success(f"{icon} **Resumo final: {status_curto}.** {explicacao}")
        elif status_curto in ("DEPENDE DO PORTE", "PROJETO ESPECIAL", "POSSÍVEL PELA VIA", "SEM DADO"):
            st.warning(f"{icon} **Resumo final: {status_curto}.** {explicacao}")
        else:
            st.error(f"{icon} **Resumo final: {status_curto}.** {explicacao}")
    st.markdown("**Mesmo quando o resultado for positivo, ainda é necessário cumprir TO, TP, IA, recuos, altura e as demais regras aplicáveis.**")

    st.markdown("---\n### 🧭 3️⃣ O que essa zona permite neste terreno?")
    if desc and desc.get("description_text"):
        title = str(desc.get("title") or zona).strip()
        if title.upper() == (zona or "").upper():
            zone_head = zona
        elif title.upper().startswith((zona or "").upper() + " —") or title.upper().startswith((zona or "").upper() + " -"):
            zone_head = title
        else:
            zone_head = f"{zona} — {title}"
        st.markdown(f"**{zone_head}**")
        st.markdown(str(desc.get("description_text")))
    else:
        st.markdown(
            f"- **Zona:** {zona or '—'}\n"
            f"- **Via do terreno:** {via}\n"
            f"- **Tipo de via:** {via_tipo_txt or '—'}"
        )
    st.markdown("**É essa leitura da zona que ajuda a entender o que pode ser implantado no lote e com qual porte.**")

    st.markdown("---\n### 📘 4️⃣ Como funciona a leitura da adequabilidade no multifamiliar?")
    st.markdown(
        "**No multifamiliar, o resultado não depende só do nome da zona. Em alguns casos, também é preciso observar o porte do empreendimento e o tipo da via. "
        "Por isso, estas siglas ajudam a interpretar corretamente a viabilidade mostrada acima.**"
    )
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            "| Sigla | O que significa | Como interpretar |\n"
            "|---|---|---|\n"
            "| **A** | Adequado / permitido | Pode seguir com o projeto, respeitando as demais regras. |\n"
            "| **I** | Inadequado / não permitido | Em regra, não pode nesse local/condição. |\n"
            "| **AP** | Adequado (pequeno porte) | Pode, mas normalmente limitado a porte pequeno. |\n"
            "| **AM** | Adequado (médio porte) | Pode, mas normalmente limitado a porte médio. |\n"
            "| **AP/AM** | Depende do porte | Pode, mas depende se o caso é pequeno ou médio. |\n"
            "| **PE** | Projeto especial | Pode exigir análise específica e condições extras no licenciamento. |"
        )
    with col2:
        st.markdown(
            "| Porte | Faixa (área construída total) |\n"
            "|---|---|\n"
            "| **Pequeno** | até **250 m²** |\n"
            "| **Médio** | de **250,01 m²** até **1.000 m²** |\n"
            "| **Grande** | de **1.000,01 m²** até **5.000 m²** |\n"
            "| **Projeto especial** | acima de **5.000 m²** |"
        )

    st.markdown("---\n### 📏 5️⃣ Regras principais para este terreno")
    st.markdown("**Depois de entender se o uso é permitido, o próximo passo é ver as regras básicas da zona para começar o estudo.**")
    if not rule:
        st.warning("Ainda não temos uma regra específica do multifamiliar carregada do Supabase para esta zona. Os próximos limites precisam ser confirmados diretamente no licenciamento e nos anexos da lei.")
    else:
        st.markdown(
            f"- **TO máxima:** {_fmt_pct(to_max_pct)}\n"
            f"- **TP mínima:** {_fmt_pct(tp_min_pct)}\n"
            f"- **IA máximo:** {_fmt_num(ia_max, 2) if ia_max not in (None, '') else '—'}\n"
            f"- **IA mínimo:** {_fmt_num(ia_min, 2) if ia_min not in (None, '') else 'não informado'}\n"
            f"- **Recuo frontal:** {_fmt_num(rec_fr)} m\n"
            f"- **Recuo lateral:** {_fmt_num(rec_lat)} m\n"
            f"- **Recuo de fundos:** {_fmt_num(rec_fun)} m\n"
            f"- **Altura permitida máxima da zona:** {_fmt_num(gabarito_f)} m\n"
            f"- **Área mínima do lote:** {_fmt_num(area_min)} m²\n"
            f"- **Testada mínima:** {_fmt_num(testada_min)} m"
        )
    st.markdown("**Esses são os parâmetros que mais influenciam o estudo inicial do projeto.**")

    st.markdown("---\n### 📐 6️⃣ Quanto posso ocupar no térreo?")
    if to_max_pct in (None, "") or to_m2 is None:
        st.info("Ainda não foi possível calcular a ocupação máxima no térreo com base na regra carregada.")
    else:
        st.markdown(f"A zona permite ocupar até **{_fmt_pct(to_max_pct)}** do terreno no térreo.")
        _formula_box(f"{_fmt_num(lot_area_f)} × {_fmt_pct(to_max_pct)} = {_fmt_num(to_m2)}")
        st.markdown("Esse é o limite máximo permitido pela Taxa de Ocupação (TO).")
        if built_ground is not None and built_ground > 0:
            st.markdown(f"A área construída pretendida informada foi de **{_fmt_num(built_ground)} m²**.")

        if is_r21:
            st.markdown(
                f"No caso do **R2.1**, quando a zona admitir leitura semelhante ao unifamiliar, o teto urbanístico do térreo pode chegar a **{_fmt_num(to_m2)} m²** pela TO."
            )
            if built_ground is not None and a_adotada is not None:
                if built_ground > a_adotada:
                    st.markdown(
                        f"Como a área pretendida de **{_fmt_num(built_ground)} m²** excede esse limite, o relatório adotou **{_fmt_num(a_adotada)} m²** como base para os cálculos."
                    )
                else:
                    st.markdown(
                        f"Como a área pretendida de **{_fmt_num(built_ground)} m²** está dentro do limite admissível, o relatório adotou esse mesmo valor como base para os cálculos."
                    )
            if A_recuos is not None:
                st.markdown(f"Se você optar por aplicar integralmente os recuos da zona, a implantação prática no térreo cai para **{_fmt_num(A_recuos)} m²**.")
            st.markdown(
                "👉 **Leitura específica do R2.1:** quando a zona permitir esse enquadramento, a implantação pode seguir lógica semelhante à do unifamiliar para parâmetros como TO, TP, IA e recuos."
            )
        else:
            st.markdown(
                f"No caso do **{_tipo_multifamiliar_label(multi_tipo, use_type_code).split(' — ')[0]}**, além da TO máxima, a implantação também precisa respeitar os **recuos obrigatórios da zona**."
            )
            if built_ground is not None and a_adotada is not None:
                if built_ground > a_adotada:
                    st.markdown(
                        f"Como a área pretendida de **{_fmt_num(built_ground)} m²** excede o limite admissível neste cenário, o relatório adotou **{_fmt_num(a_adotada)} m²** como base para os cálculos."
                    )
                else:
                    st.markdown(
                        f"Como a área pretendida de **{_fmt_num(built_ground)} m²** está dentro do limite admissível, o relatório adotou esse mesmo valor como base para os cálculos."
                    )
            st.markdown(
                f"### Recuos da zona\n"
                f"- **Frontal:** {_fmt_num(rec_fr)}\n"
                f"- **Laterais:** {_fmt_num(rec_lat)}\n"
                f"- **Fundo:** {_fmt_num(rec_fun)}"
            )

        if W_util is not None and D_util is not None and A_recuos is not None:
            st.markdown(f"### Cálculo da largura útil\nA largura original do lote é de **{_fmt_num(lot_front)} m**.")
            _formula_box(f"{_fmt_num(lot_front)} − recuos laterais = {_fmt_num(W_util)}")
            st.markdown(f"**Largura útil: {_fmt_num(W_util)}**")
            st.markdown(f"### Cálculo da profundidade útil\nA profundidade original do lote é de **{_fmt_num(lot_depth)} m**.")
            _formula_box(f"{_fmt_num(lot_depth)} − recuo frontal − recuo de fundo = {_fmt_num(D_util)}")
            st.markdown(f"**Profundidade útil: {_fmt_num(D_util)}**")
            st.markdown("### Cálculo da área útil de implantação")
            _formula_box(f"{_fmt_num(W_util)} × {_fmt_num(D_util)} = {_fmt_num(A_recuos)}")

        if a_adotada is not None and to_utilizada_pct is not None:
            st.markdown("**TO efetiva considerada no relatório**")
            _formula_box(f"{_fmt_num(a_adotada)} ÷ {_fmt_num(lot_area_f)} = {_fmt_pct(to_utilizada_pct)}")
            st.markdown(f"**TO do projeto considerada no relatório: {_fmt_pct(to_utilizada_pct)}**")
            if built_ground is not None and built_ground > a_adotada:
                leitura_base = f"Como a área pedida foi de **{_fmt_num(built_ground)} m²**"
            else:
                leitura_base = f"Como a área adotada no relatório foi de **{_fmt_num(a_adotada)} m²**"
            if is_r21:
                complemento = f"Caso sejam aplicados integralmente os recuos da zona, a implantação prática cai para **{_fmt_num(A_recuos)} m²**." if A_recuos is not None else ""
                st.markdown(
                    f"👉 **Leitura prática:** pela TO, o lote pode chegar até **{_fmt_num(to_m2)} m²** no térreo. {leitura_base}, o relatório adotou **{_fmt_num(a_adotada)} m²** como limite urbanístico para os cálculos. {complemento}"
                )
            else:
                complemento = f"Ao aplicar todos os recuos da zona, o espaço que realmente sobra para implantar a edificação no térreo fica em **{_fmt_num(A_recuos)} m²**." if A_recuos is not None else ""
                st.markdown(
                    f"👉 **Leitura prática:** pela TO, o lote poderia ocupar até **{_fmt_num(to_m2)} m²** no térreo. {leitura_base}, o relatório adotou **{_fmt_num(a_adotada)} m²** para os cálculos deste cenário. {complemento}"
                )

    st.markdown("---\n### 🌿 7️⃣ Quanto preciso deixar livre?")
    if tp_min_pct is None or tp_m2 is None:
        st.info("Ainda não foi possível calcular a Taxa de Permeabilidade com base na regra carregada.")
    else:
        st.markdown(f"A zona exige **{_fmt_pct(tp_min_pct)}** de área permeável.")
        _formula_box(f"{_fmt_num(lot_area_f)} × {_fmt_pct(tp_min_pct)} = {_fmt_num(tp_m2)} obrigatórios permeáveis")
        st.markdown("Isso quer dizer que parte do terreno precisa continuar permitindo a infiltração da água da chuva no solo.")
        if a_adotada is not None and area_livre_projeto is not None:
            st.markdown("**Área livre considerando a área adotada no relatório**")
            st.markdown(
                f"Como o relatório adotou **{_fmt_num(a_adotada)} m²** no térreo, a área livre remanescente no lote fica assim:\n\n"
                f"👉 **{_fmt_num(lot_area_f)} m² − {_fmt_num(a_adotada)} m² = {_fmt_num(area_livre_projeto)} m²**"
            )
            st.markdown(f"**Área livre remanescente no lote: {_fmt_num(area_livre_projeto)} m²**")
            st.markdown(f"Desses, **{_fmt_num(tp_m2)} m²** precisam permanecer permeáveis.")
            if area_impermavel_pos_tp is not None:
                st.markdown(
                    f"Assim, restam:\n\n👉 **{_fmt_num(area_livre_projeto)} m² − {_fmt_num(tp_m2)} m² = {_fmt_num(area_impermavel_pos_tp)} m²**\n\n"
                    f"**Área que ainda pode receber piso impermeável: {_fmt_num(area_impermavel_pos_tp)} m²**"
                )
            leitura_tp = (
                f"como a área pretendida inicial de **{_fmt_num(built_ground)} m²** excedeu o limite adotado no relatório, os cálculos passaram a considerar **{_fmt_num(a_adotada)} m²** no térreo"
                if (built_ground is not None and built_ground > a_adotada)
                else f"os cálculos passaram a considerar a própria área pretendida informada, de **{_fmt_num(a_adotada)} m²** no térreo"
            )
            st.markdown(
                f"👉 **Leitura prática:** {leitura_tp}. Com isso, a área livre remanescente fica em **{_fmt_num(area_livre_projeto)} m²**, "
                f"dos quais **{_fmt_num(tp_m2)} m²** devem permanecer permeáveis para atender à exigência mínima da zona."
            )

    st.markdown("---\n### 🏢 8️⃣ Posso construir mais andares?")
    if ia_max in (None, "") or ia_m2 is None:
        st.info("Ainda não foi possível calcular o potencial total de construção com base no IA da zona.")
    else:
        st.markdown(
            "Além da ocupação no térreo, a zona também define o potencial construtivo total do lote por meio do **Índice de Aproveitamento (IA)**."
        )
        st.markdown(f"**Índice de Aproveitamento (IA): {_fmt_num(ia_max, 2)}**")
        _formula_box(f"{_fmt_num(lot_area_f)} × {_fmt_num(ia_max, 2)} = {_fmt_num(ia_m2)} no total")
        st.markdown(f"Isso significa que você pode distribuir até **{_fmt_num(ia_m2)}** somando todos os pavimentos.")
        if a_adotada is not None and ia_saldo is not None:
            st.markdown(
                f"Como o relatório adotou **{_fmt_num(a_adotada)} m²** no térreo, o saldo estimado para crescer acima fica assim:\n\n"
                f"👉 **{_fmt_num(ia_m2)} m² − {_fmt_num(a_adotada)} m² = {_fmt_num(ia_saldo)} m²**\n\n"
                f"**Saldo estimado para pavimentos superiores: {_fmt_num(ia_saldo)} m²**"
            )
            st.markdown(
                f"👉 **Leitura prática:** considerando a área adotada de **{_fmt_num(a_adotada)} m²** no térreo, ainda restam **{_fmt_num(ia_saldo)} m²** de potencial construtivo pelo IA para crescimento em pavimentos superiores, desde que o projeto respeite também altura máxima, recuos, ventilação, iluminação, circulação e demais exigências aplicáveis."
            )
        st.markdown(f"**Altura permitida máxima da zona: {_fmt_num(gabarito_f)}**")
        if pav_est:
            st.markdown(
                "**Estimativa simples para ter noção do número de pavimentos:**  \
"
                "essa leitura serve apenas como referência inicial. O número real de andares depende do projeto, do pé-direito adotado, "
                "da estrutura, da circulação vertical e das demais exigências aplicáveis."
            )

    st.markdown("---\n### 🚗 9️⃣ Vagas de estacionamento")
    st.markdown(
        "**A quantidade de vagas depende do tamanho da unidade habitacional.**\n\n"
        "Regras:\n"
        "- apartamento com menos de **90 m²** → **1 vaga por unidade**\n"
        "- apartamento com **90 m²** ou mais → **1,5 vaga por unidade**\n\n"
        "**Quando aparecer 1,5, o total final deve ser arredondado para cima.**\n\n"
        "**Informação importante:**\n"
        "- pode haver **redução de até 20% das vagas** se o imóvel estiver em raio de **250 m do VLT**;\n"
        "- **Art. 121, § 4º:** “Poderá ser utilizada até **30%** (trinta por cento) das vagas de estacionamento previstas para estacionamento de motocicletas.”\n\n"
        f"👉 **Na prática:** como o **{_tipo_multifamiliar_label(multi_tipo, use_type_code).split(' — ')[0]}** é multifamiliar, essa lógica de vagas entra no cálculo do estudo."
    )

    render_quadro_tecnico()
    st.markdown("---\n### 🚶 1️⃣1️⃣ O que preciso saber sobre a calçada?")
    st.markdown("**A análise do terreno não termina dentro do lote. Também existem regras para calçada, acesso ao imóvel, rebaixo de meio-fio e relação com a rua.**")
    render_figuras_anexo_v(rule or {}, is_corner=bool(st.session_state.get("lot_is_corner") or calc.get("lot_is_corner")))

    st.markdown("---\n### 💡 1️⃣2️⃣ Dicas valiosas")
    _render_dicas_valiosas(multi_tipo, use_type_code)

    st.markdown("---\n### 📌 1️⃣3️⃣ Resumo rápido final")
    st.markdown("Se você quiser ver só o essencial deste terreno, este é o resumo principal:")
    resumo_uso = uso_label
    if multi_tipo in ("R22", "R2.2", "R2_2") or use_type_code.endswith("R22"):
        resumo_uso = "R2.2 — condomínio horizontal com via interna"
    if multi_tipo in ("R3", "R03") or use_type_code.endswith("R3"):
        resumo_uso = "R3 — residência multifamiliar vertical"
    resumo_extra = ""
    if built_ground is not None and a_adotada is not None:
        resumo_extra += f"\n- **Área pretendida informada:** {_fmt_num(built_ground)} m²"
        resumo_extra += f"\n- **Área adotada no relatório:** {_fmt_num(a_adotada)} m²"
        if to_utilizada_pct is not None:
            resumo_extra += f"\n- **TO efetiva considerada:** {_fmt_pct(to_utilizada_pct)}"
        if area_livre_projeto is not None:
            resumo_extra += f"\n- **Área livre remanescente:** {_fmt_num(area_livre_projeto)} m²"
        if ia_saldo is not None:
            resumo_extra += f"\n- **Saldo estimado pelo IA:** {_fmt_num(ia_saldo)} m²"
    st.markdown(
        f"- **Uso analisado:** {resumo_uso}\n"
        f"- **Zona:** {zone_label or zona}\n"
        f"- **Tipo de lote:** {tipo_lote}\n"
        f"- **Via:** {via}\n"
        f"- **Tipo de via:** {via_tipo_txt}\n"
        f"- **Resultado final:** {icon} {status_curto}\n"
        f"- **TO máxima:** {_fmt_pct(to_max_pct)}\n"
        f"- **TP mínima:** {_fmt_pct(tp_min_pct)}\n"
        f"- **IA máximo:** {_fmt_num(ia_max, 2) if ia_max not in (None, '') else '—'}\n"
        f"- **Altura permitida máxima:** {_fmt_num(gabarito_f)} m"
        f"{resumo_extra}"
    )
    tipo_sigla = "R2.1" if (multi_tipo in ("R21","R2.1","R2_1") or use_type_code.endswith("R21")) else ("R2.2" if (multi_tipo in ("R22","R2.2","R2_2") or use_type_code.endswith("R22")) else "R3")
    if built_ground is not None and a_adotada is not None:
        if built_ground > a_adotada:
            st.markdown(
                f"👉 **Em resumo:** o uso residencial multifamiliar **{tipo_sigla}** foi considerado **{status_curto.lower()}** neste terreno. "
                f"Você informou **{_fmt_num(built_ground)} m²** no térreo, mas o relatório adotou **{_fmt_num(a_adotada)} m²** para respeitar os limites urbanísticos deste cenário. "
                f"Com isso, a TO considerada ficou em **{_fmt_pct(to_utilizada_pct)}**, a área livre remanescente em **{_fmt_num(area_livre_projeto)} m²** e o saldo estimado pelo IA em **{_fmt_num(ia_saldo)} m²**."
            )
        else:
            st.markdown(
                f"👉 **Em resumo:** o uso residencial multifamiliar **{tipo_sigla}** foi considerado **{status_curto.lower()}** neste terreno. "
                f"O relatório considerou a área pretendida de **{_fmt_num(a_adotada)} m²** no térreo, com TO efetiva de **{_fmt_pct(to_utilizada_pct)}**, "
                f"área livre remanescente de **{_fmt_num(area_livre_projeto)} m²** e saldo estimado pelo IA de **{_fmt_num(ia_saldo)} m²**."
            )
    else:
        st.markdown(
            "👉 **Em resumo:**\n"
            f"- o uso residencial multifamiliar **{tipo_sigla}** foi considerado **{status_curto.lower()}** neste terreno;\n"
            f"- a zona permite ocupar até **{_fmt_pct(to_max_pct)}** do lote no térreo;\n"
            f"- pelo menos **{_fmt_pct(tp_min_pct)}** do terreno precisa continuar permeável;\n"
            f"- a construção pode chegar até **{_fmt_num(ia_max, 2) if ia_max not in (None, '') else '—'}** vezes a área do lote no total;\n"
            f"- e a altura deve respeitar o limite máximo permitido da zona."
        )

    st.markdown("---\n### 🏛️ 1️⃣4️⃣ O que acontece depois desta etapa?")
    _render_alvara_section()

    st.markdown("---\n### ✅ 1️⃣5️⃣ Fechamento final")
    st.markdown(
        "**Este relatório foi pensado para ajudar você a entender o terreno de forma mais simples.**\n\n"
        "**Na etapa de projeto e aprovação, ainda será preciso conferir os detalhes completos no licenciamento.**"
    )
