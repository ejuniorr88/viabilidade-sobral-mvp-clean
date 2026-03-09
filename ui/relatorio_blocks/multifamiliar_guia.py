from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, List

import streamlit as st


def _get_supabase():
    try:
        from core.supabase_client import get_supabase  # type: ignore
        return get_supabase()
    except Exception:
        return None


def _norm(s: Any) -> str:
    return str(s or "").strip().upper()


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
    """Gera variações para bater com possíveis formatos do banco (ex.: 'ZEPE 1' vs 'ZEPE1')."""
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
    return None  # via local / outras não entram na tabela por tipo de via


def _fetch_adequabilidade(
    *, zone_sigla: str, via_tipo_texto: Optional[str], use_type_code: str
) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
    """Busca adequabilidade por zona (2A) e por tipo de via (arterial/coletora)."""
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

    # Zona (Quadro 2A - sede)
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

    # Tipo de via (arterial/coletora) — quando aplicável
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


def render_multifamiliar_guia(*, calc: Dict[str, Any], rule: Optional[Dict[str, Any]] = None, **_: Any) -> None:
    multi_tipo = _norm(calc.get("multi_tipo"))
    use_type_code = _norm(calc.get("use_type_code"))

    st.subheader("Multifamiliar — Fase 1 (Guia do Projetista)")
    st.caption("Guia rápido para iniciar o projeto — sem cálculo final de unidades/áreas. (LC 91/2023 e LC 90/2023)")

    # A) Adequabilidade
    st.markdown("### A) Pode / não pode (adequabilidade)")

    zona = _norm(calc.get("zone") or calc.get("zone_sigla"))
    via_tipo_txt = calc.get("via_tipo") or calc.get("via_type") or ""

    zone_class, via_class, dbg = _fetch_adequabilidade(
        zone_sigla=zona,
        via_tipo_texto=via_tipo_txt,
        use_type_code=use_type_code,
    )

    if not zone_class and not via_class:
        st.info(
            "Adequabilidade ainda não foi encontrada no banco para este uso/zona/via. "
            "Confira se as tabelas `adequab_zonas_sede` e `adequab_vias` estão com dados."
        )
        with st.expander("🔎 Diagnóstico (para conferência)"):
            st.json(dbg)
    else:
        # Explicação leiga (antes do resultado)
        st.markdown("**Como interpretar este resultado (bem simples):**")
        st.markdown(
            "- Para **residência multifamiliar**, a permissão pode depender de **duas coisas**:\n"
            "  1) **Resultado por ZONA** (onde o lote está localizado)\n"
            "  2) **Resultado por TIPO DE VIA** (arterial/coletora e paisagísticas), quando a via for desse tipo\n\n"
            "**Regra prática (para não errar):**\n"
            "- Se o **resultado da ZONA** for **I (Inadequado / não permitido)** e a via for **VIA LOCAL**, então **continua I** (não permitido).\n"
            "- Se a via for **ARTERIAL/COLETORA**, o licenciamento pode considerar também o **resultado por tipo de via**.\n"
            "  Mesmo quando der permitido, ainda é obrigatório cumprir TO/TP/IA/recuos/altura e outras restrições (ex.: ZEIA/APP).\n\n"
            "**Exemplos rápidos:**\n"
            "- **ZONA: I (Inadequado)** + **VIA: local** → **NÃO PERMITE**\n"
            "- **ZONA: I (Inadequado)** + **VIA: coletora/arterial** → pode mudar conforme o **resultado por tipo de via** (depende do licenciamento)"
        )

        if zone_class:
            st.success(f"✅ Por zona (2A): **{zona} → {zone_class} ({_sigla_nome(zone_class)})**")
        else:
            st.warning("⚠️ Por zona (2A): não encontrado para esta zona.")

        via_norm = _via_tipo_norm(via_tipo_txt)
        if via_norm:
            if via_class:
                st.success(f"✅ Por tipo de via: **{via_norm} → {via_class} ({_sigla_nome(via_class)})**")
            else:
                st.warning(f"⚠️ Por tipo de via: não encontrado para **{via_norm}**.")
        else:
            st.success("✅ **Via identificada como VIA LOCAL.** Nessa situação, a tabela por tipo de via (arterial/coletora/paisagística) geralmente não se aplica — normalmente vale o resultado da **zona**.")

        
        # -------------------------
        # 3) Resumo final (bem leigo)
        # -------------------------
        def _resumo_final(zone_class: Optional[str], via_norm: Optional[str], via_class: Optional[str]) -> Tuple[str, str, str]:
            zc = _norm(zone_class)
            vc = _norm(via_class)
            # via local -> vale a zona
            if not via_norm:
                if zc in ("AP", "AM", "AP/AM"):
                    return ("DEPENDE", "⚠️", "Depende do porte (pequeno/médio) indicado pela zona. Veja a tabela de **porte** logo abaixo.")
                if zc == "PE":
                    return ("DEPENDE", "⚠️", "Pode exigir análise específica no licenciamento (projeto especial).")
                if zc == "I":
                    return ("NÃO PERMITE", "❌", "A zona não permite este uso, e por ser via local, vale a regra da zona.")
                if zc == "A":
                    return ("PERMITE", "✅", "A zona permite este uso, e por ser via local, vale a regra da zona.")
                return ("DEPENDE", "⚠️", "Faltam dados suficientes para concluir (verifique a zona/SEUMA).")

            # vias arteriais/coletoras/paisagísticas -> pode ter 2 camadas
            if zc in ("AP", "AM", "AP/AM"):
                return ("DEPENDE", "⚠️", "Depende do porte (pequeno/médio). Veja a tabela de **porte** logo abaixo e depois confirme TO/TP/IA/recuos/altura.")
            if zc == "PE":
                return ("DEPENDE", "⚠️", "Pode exigir análise específica no licenciamento (projeto especial).")
            if zc == "A" and vc == "A":
                return ("PERMITE", "✅", "Zona e tipo de via permitem. Ainda é obrigatório cumprir TO/TP/IA/recuos/altura.")
            if zc == "A" and vc == "I":
                return ("NÃO PERMITE", "❌", "A zona permite, mas o tipo de via restringe — no licenciamento, pode não ser aceito.")
            if zc == "I" and vc == "A":
                return ("DEPENDE", "⚠️", "A zona restringe, mas o tipo de via permite — isso pode depender do licenciamento.")
            if zc == "I" and (vc == "I" or not vc):
                return ("NÃO PERMITE", "❌", "A zona não permite este uso (e a via não libera).")
            return ("DEPENDE", "⚠️", "Faltam dados suficientes para concluir (verifique a zona/SEUMA).")

        status_lbl, status_ico, status_msg = _resumo_final(zone_class, via_norm, via_class)
        if status_lbl == "PERMITE":
            st.success(f"**{status_ico} Resumo final: {status_lbl}.** {status_msg}")
        elif status_lbl == "NÃO PERMITE":
            st.error(f"**{status_ico} Resumo final: {status_lbl}.** {status_msg}")
        else:
            st.warning(f"**{status_ico} Resumo final: {status_lbl}.** {status_msg}")


# Se aparecer AP/AM (depende do porte), explicar como decidir
if _norm(zone_class) in ("AP", "AM", "AP/AM") or _norm(via_class) in ("AP", "AM", "AP/AM"):
    st.info(
        "📌 **Como decidir o porte (bem simples):** o *porte* normalmente é definido pela **área construída total (m²)** do empreendimento. "
        "Use a tabela **"O que é porte"** logo abaixo para enquadrar como **Pequeno / Médio / Grande**. "
        "Depois, confirme também TO/TP/IA/recuos/altura no licenciamento."
    )

# Explicação leiga das categorias de via
        st.markdown("**O que é via local, coletora, arterial, etc.? (bem simples)**")
        st.markdown(
            "- **Via local:** rua de bairro, usada principalmente para acesso às casas/quadras (tráfego menor).\n"
            "- **Via coletora:** rua que **coleta** o tráfego das vias locais e leva para vias maiores.\n"
            "- **Via arterial:** via principal, de maior fluxo, que liga áreas/bairros e distribui o tráfego na cidade.\n"
            "- **Paisagística:** classificação usada pela lei quando a via tem tratamento urbano/paisagístico específico."
        )

        # Dois quadros lado a lado (siglas x porte)
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**O que significam as siglas (bem simples):**")
            st.markdown(
                "| Sigla | O que significa | Como interpretar |\n"
                "|---|---|---|\n"
                "| **A** | Adequado / permitido | Pode seguir com o projeto (respeitando TO/TP/IA/recuos). |\n"
                "| **I** | Inadequado / não permitido | Em regra, **não pode** nesse local/condição. |\n"
                "| **AP** | Adequado (pequeno porte) | Pode, mas normalmente limitado a porte pequeno. |\n"
                "| **AM** | Adequado (médio porte) | Pode, mas normalmente limitado a porte médio. |\n"
                "| **AP/AM** | Depende do porte | Pode, mas depende se o seu caso é pequeno ou médio. |\n"
                "| **PE** | Projeto especial | Pode exigir análise específica/condições extras no licenciamento. |\n"
            )

        with col2:
            st.markdown("**O que é “porte” (pequeno / médio / grande)?**")
            st.caption("Porte é a escala do empreendimento, normalmente definida pela **área construída total (m²)**.")
            st.markdown(
                "| Porte | Faixa (área construída total) |\n"
                "|---|---|\n"
                "| **Pequeno** | até **250 m²** |\n"
                "| **Médio** | de **250,01 m²** até **1.000 m²** |\n"
                "| **Grande** | de **1.000,01 m²** até **5.000 m²** |\n"
                "| **Projeto especial** | acima de **5.000 m²** |\n"
            )
            st.caption("Obs.: se a lei/SEUMA adotar critério diferente para algum uso específico, prevalece o licenciamento.")

    # B) Parâmetros urbanísticos
    st.markdown("### B) Parâmetros urbanísticos (para começar projeto)")
    if not rule:
        st.warning(
            "Ainda não temos uma **regra específica do multifamiliar** cadastrada no Supabase para esta zona.\n\n"
            "**O que isso quer dizer na prática?**\n"
            "- O sistema não consegue confirmar automaticamente TO/TP/IA/recuos/gabarito para o multifamiliar aqui.\n"
            "- Você pode começar o estudo, mas antes de fechar o projeto, confirme esses limites no licenciamento da **SEUMA** e nos anexos da lei.\n\n"
            "**Dica rápida:**\n"
            "- **TO** = quanto pode ocupar no térreo\n"
            "- **TP** = quanto precisa deixar permeável\n"
            "- **IA** = total máximo construído somando pavimentos"
        )
    else:
        def _pct(v: Any) -> Optional[float]:
            try:
                if v is None or v == "":
                    return None
                f = float(v)
                return f * 100 if f <= 1 else f
            except Exception:
                return None

        to_max = _pct(rule.get("to_max")) or _pct(rule.get("to_max_pct"))
        tp_min = _pct(rule.get("tp_min")) or _pct(rule.get("tp_min_pct"))
        ia_max = rule.get("ia_max")

        c1, c2, c3 = st.columns(3)
        c1.metric("TO máxima", f"{to_max:.0f}%" if isinstance(to_max, (int, float)) else "—")
        c2.metric("TP mínima", f"{tp_min:.0f}%" if isinstance(tp_min, (int, float)) else "—")
        c3.metric("IA máximo", f"{ia_max}" if ia_max not in (None, "") else "—")

        st.caption("Demais recuos/gabarito/testadas seguem a regra carregada do Supabase para esta zona.")

    # C) Checklist do tipo escolhido
    st.markdown("### C) Checklist do tipo escolhido (sem exigir projeto pronto)")

    if multi_tipo in ("R21", "R2.1", "R2_1") or use_type_code.endswith("R21"):
        st.markdown("**R2.1 — 2 unidades no mesmo lote (justapostas ou sobrepostas)**")
        st.markdown(
            "- ✅ **Altura/andares:** pode ter no máximo 2 pavimentos (ex.: térreo + 1º andar). *(LC 91/2023 — definição de R2.1)*\n"
            "- ✅ **Justapostas (lado a lado):** testada mínima 8,00 m (exceto ZEIS). *(LC 91/2023 — requisito citado para R2.1)*\n"
            "- ✅ **Parâmetros urbanísticos:** quando a zona permitir, pode usar os parâmetros do unifamiliar, respeitando adequabilidade. *(LC 91/2023 — Art. 106)*"
        )
    elif multi_tipo in ("R22", "R2.2", "R2_2") or use_type_code.endswith("R22"):
        st.markdown("**R2.2 — Condomínio horizontal (via interna)**")
        st.markdown(
            "- ✅ Acesso de veículos: abertura mínima 4,00 m (largura) e 4,50 m (altura livre).\n"
            "- ✅ Via interna: largura mínima 6,00 m.\n"
            "- ✅ Muro frontal: pelo menos 25% em gradil/visibilidade.\n"
            "- ✅ Resíduos: local no alinhamento com abertura para o logradouro.\n"
            "- ✅ Áreas comuns: acessibilidade + sanitários/copa funcionários + DML.\n"
            "- ⚠️ Lazer: se passar de 10 unidades, prever lazer mínimo conforme lei. *(LC 90/2023 — Art. 168)*"
        )
    elif multi_tipo in ("R3", "R03") or use_type_code.endswith("R3"):
        st.markdown("**R3 — Condomínio vertical (edifício)**")
        st.markdown(
            "- ✅ Muro frontal: pelo menos 50% em gradil/visibilidade.\n"
            "- ✅ Resíduos: local no alinhamento com abertura para o logradouro.\n"
            "- ✅ Áreas comuns: acessibilidade + sanitários/copa + DML.\n"
            "- ⚠️ Lazer: prever lazer mínimo conforme lei.\n"
            "- ⚠️ Entregas/recepção: se passar de 30 unidades, prever espaço mínimo.\n"
            "- ⚠️ EIV: se passar de 100 unidades, EIV pode ser exigido. *(LC 90/2023 — Art. 170; LC 91/2023 — Art. 88)*"
        )
    else:
        st.info("Selecione o tipo de multifamiliar (R2.1 / R2.2 / R3) no Item 2 para exibir o checklist.")

    # D) Vagas
    st.markdown("### D) Vagas de estacionamento (como calcular)")
    st.markdown(
        "A quantidade de vagas depende do tamanho do apartamento (área construída da unidade):\n\n"
        "- 🚗 Apartamento com menos de 90 m² → 1 vaga por unidade\n"
        "- 🚗 Apartamento com 90 m² ou mais → 1,5 vaga por unidade\n\n"
        "📌 Quando aparece 1,5, o total final deve ser arredondado para cima (não existe “meia vaga”).\n\n"
        "*(LC 90/2023 — Anexo IV)*"
    )
    st.markdown("**Exemplo rápido:**")
    st.markdown(
        "- 10 apartamentos com 80 m² → 10 vagas\n"
        "- 11 apartamentos com 100 m² → 11 × 1,5 = 16,5 → 17 vagas"
    )

    # Aviso informativo quadra máxima
    if multi_tipo in ("R22", "R2.2", "R2_2", "R3", "R03") or use_type_code.endswith(("R22", "R3")):
        st.markdown("---")
        st.markdown(
            "**Atenção (informativo):** Para projetos multifamiliares **R2.2** (condomínio horizontal) e **R3** (condomínio vertical), "
            "a legislação menciona uma verificação relacionada à **“quadra máxima” da zona**. "
            "Em caso de dúvida, consulte o licenciamento junto à **SEUMA** e os **anexos da lei**. "
            "*(Referência: **LC 91/2023**, requisito citado para R2.2 e R3.)*"
        )
