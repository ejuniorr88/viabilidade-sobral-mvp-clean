from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import streamlit as st


def _get_supabase():
    """Tenta obter cliente Supabase do projeto (sem quebrar o app se não existir)."""
    try:
        from core.supabase_client import get_supabase  # type: ignore
        return get_supabase()
    except Exception:
        return None


def _norm_zone_sigla(z: Any) -> str:
    return str(z or "").strip().upper()


def _norm_use_type_code(u: Any) -> str:
    return str(u or "").strip().upper()


def _norm_via_tipo(v: Any) -> Optional[str]:
    """Mapeia o texto do app para os tipos usados na tabela adequab_vias."""
    s = str(v or "").strip().lower()
    if not s:
        return None

    # exemplos comuns no app: "via local", "arterial", "coletora", etc.
    if "arterial" in s and "pais" in s:
        return "ARTERIAL_PAISAGISTICA"
    if "coletora" in s and "pais" in s:
        return "COLETORA_PAISAGISTICA"
    if "arterial" in s:
        return "ARTERIAL"
    if "coletora" in s:
        return "COLETORA"

    # via local / outras: não existe no Quadro I do Excel
    return None


def _fetch_adequabilidade(
    *,
    zone_sigla: str,
    via_tipo_texto: Optional[str],
    use_type_code: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Busca adequabilidade por zona (sede) e por categoria viária."""
    sb = _get_supabase()
    if sb is None:
        return None, None

    zona = _norm_zone_sigla(zone_sigla)
    use_code = _norm_use_type_code(use_type_code)
    via_tipo = _norm_via_tipo(via_tipo_texto)

    zone_class = None
    via_class = None

    try:
        # Por enquanto: sempre usa a tabela de SEDE (Quadro 2A),
        # porque você decidiu NÃO usar Sede/Distrito agora.
        res = (
            sb.table("adequab_zonas_sede")
            .select("classificacao")
            .eq("use_type_code", use_code)
            .eq("zone_sigla", zona)
            .limit(1)
            .execute()
        )
        data = getattr(res, "data", None) or []
        if data:
            zone_class = (data[0].get("classificacao") or "").strip()
    except Exception:
        zone_class = None

    if via_tipo:
        try:
            res2 = (
                sb.table("adequab_vias")
                .select("classificacao")
                .eq("use_type_code", use_code)
                .eq("via_tipo", via_tipo)
                .limit(1)
                .execute()
            )
            data2 = getattr(res2, "data", None) or []
            if data2:
                via_class = (data2[0].get("classificacao") or "").strip()
        except Exception:
            via_class = None

    return zone_class, via_class


def render_multifamiliar_guia(*, calc: Dict[str, Any], rule: Optional[Dict[str, Any]] = None, **_: Any) -> None:
    """Multifamiliar — Fase 1 (Guia do Projetista)."""

    multi_tipo = (calc.get("multi_tipo") or "").upper()
    use_type_code = (calc.get("use_type_code") or "").upper()

    st.subheader("Multifamiliar — Fase 1 (Guia do Projetista)")
    st.caption("Guia rápido para iniciar o projeto — sem cálculo final de unidades/áreas. (LC 91/2023 e LC 90/2023)")

    # -------------------------
    # A) Adequabilidade
    # -------------------------
    st.markdown("### A) Pode / não pode (adequabilidade)")

    zona = _norm_zone_sigla(calc.get("zone") or calc.get("zone_sigla"))
    via_tipo_txt = calc.get("via_tipo") or calc.get("via_type") or ""

    zone_class, via_class = _fetch_adequabilidade(
        zone_sigla=zona,
        via_tipo_texto=via_tipo_txt,
        use_type_code=use_type_code,
    )

    if not zone_class and not via_class:
        st.info(
            "Adequabilidade ainda não foi encontrada no banco para este uso/zona/via. "
            "Confira se as tabelas `adequab_zonas_sede` e `adequab_vias` foram preenchidas. "
            "(Quadro 2A e Quadro I)."

            "\n\nAssim que estiver cadastrada, o sistema exibirá A / I / AP / AM / PE automaticamente."
        )
    else:
        # Mostra por zona (Quadro 2A)
        if zone_class:
            st.success(f"✅ Por zona (Quadro 2A): **{zona} → {zone_class}**")
        else:
            st.warning("⚠️ Por zona (Quadro 2A): não encontrado para esta zona.")

        # Mostra por via (Quadro I), quando for arterial/coletora/paisagística
        via_norm = _norm_via_tipo(via_tipo_txt)
        if via_norm:
            if via_class:
                st.success(f"✅ Por categoria viária (Quadro I): **{via_norm} → {via_class}**")
            else:
                st.warning(f"⚠️ Por categoria viária (Quadro I): não encontrado para **{via_norm}**.")
        else:
            st.info("ℹ️ Categoria viária do Quadro I se aplica a vias **arteriais/coletoras** (e paisagísticas). Para **via local**, este quadro pode não se aplicar.")

        st.caption("Legenda: A=adequado; I=inadequado; AP/AM=depende do porte/condições; PE=projeto especial (conforme lei).")

    # -------------------------
    # B) Parâmetros urbanísticos
    # -------------------------
    st.markdown("### B) Parâmetros urbanísticos (para começar projeto)")
    if not rule:
        st.warning(
            "Regra urbanística específica do multifamiliar ainda não foi cadastrada no Supabase para esta zona.\n\n"
            "➡️ Você já pode iniciar o estudo, mas **confirme TO/TP/IA/recuos/gabarito** no licenciamento junto à **SEUMA** e nos **anexos da lei**."
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

    # -------------------------
    # C) Checklist
    # -------------------------
    st.markdown("### C) Checklist do tipo escolhido (sem exigir projeto pronto)")

    if multi_tipo in ("R21", "R2.1", "R2_1") or use_type_code.endswith("R21"):
        st.markdown("**R2.1 — 2 unidades no mesmo lote (justapostas ou sobrepostas)**")
        st.markdown(
            "- ✅ **Altura/andares:** pode ter **no máximo 2 pavimentos** (ex.: térreo + 1º andar).\n"
            "  *(LC 91/2023 — definição de R2.1)*\n"
            "- ✅ **Se for “lado a lado” (justapostas):** a **testada** (frente do lote) deve ter **pelo menos 8,00 m**.\n"
            "  *(exceto ZEIS — LC 91/2023, requisito citado para R2.1)*\n"
            "- ✅ **Regras urbanísticas (TO/TP/IA/recuos/gabarito):** quando a zona permitir, pode usar os **parâmetros do unifamiliar**,\n"
            "  sempre respeitando a **adequabilidade** do uso na zona.\n"
            "  *(LC 91/2023 — Art. 106)*"
        )
    elif multi_tipo in ("R22", "R2.2", "R2_2") or use_type_code.endswith("R22"):
        st.markdown("**R2.2 — Condomínio horizontal (via interna)**")
        st.markdown(
            "- ✅ **Acesso de veículos:** abertura mínima **4,00 m** de largura e **4,50 m** de altura livre.\n"
            "- ✅ **Via interna:** largura mínima **6,00 m**.\n"
            "- ✅ **Muro frontal:** pelo menos **25% em gradil/visibilidade**.\n"
            "- ✅ **Resíduos:** local de resíduos no alinhamento com abertura para o logradouro.\n"
            "- ✅ **Áreas comuns:** acessibilidade + sanitários/copa funcionários + DML.\n"
            "- ⚠️ **Lazer:** se passar de 10 unidades, prever lazer mínimo conforme lei.\n"
            "*(LC 90/2023 — Art. 168)*"
        )
    elif multi_tipo in ("R3", "R03") or use_type_code.endswith("R3"):
        st.markdown("**R3 — Condomínio vertical (edifício)**")
        st.markdown(
            "- ✅ **Muro frontal:** pelo menos **50% em gradil/visibilidade**.\n"
            "- ✅ **Resíduos:** local de resíduos no alinhamento com abertura para o logradouro.\n"
            "- ✅ **Áreas comuns:** acessibilidade + sanitários/copa + DML.\n"
            "- ⚠️ **Lazer:** prever lazer mínimo conforme lei.\n"
            "- ⚠️ **Entregas/recepção:** se passar de 30 unidades, prever espaço mínimo.\n"
            "- ⚠️ **EIV:** se passar de 100 unidades, EIV pode ser exigido.\n"
            "*(LC 90/2023 — Art. 170; LC 91/2023 — Art. 88)*"
        )
    else:
        st.info("Selecione o tipo de multifamiliar (R2.1 / R2.2 / R3) no Item 2 para exibir o checklist.")

    # -------------------------
    # D) Vagas
    # -------------------------
    st.markdown("### D) Vagas de estacionamento (como calcular)")
    st.markdown(
        "A quantidade de vagas depende do **tamanho do apartamento (área construída da unidade)**:\n\n"
        "- 🚗 **Apartamento com menos de 90 m²** → **1 vaga por unidade**\n"
        "- 🚗 **Apartamento com 90 m² ou mais** → **1,5 vaga por unidade**\n\n"
        "📌 Na prática, quando aparece **1,5**, o total final deve ser **arredondado para cima** "
        "(porque não existe “meia vaga”).\n\n"
        "*(LC 90/2023 — Anexo IV)*"
    )
    st.markdown("**Exemplo rápido (só para entender a lógica):**")
    st.markdown(
        "- 10 apartamentos com **80 m²** → **10 vagas**\n"
        "- 11 apartamentos com **100 m²** → 11 × 1,5 = 16,5 → **17 vagas** (arredonda pra cima)"
    )

    # Aviso informativo quadra máxima (apenas para R2.2 e R3)
    if multi_tipo in ("R22", "R2.2", "R2_2", "R3", "R03") or use_type_code.endswith(("R22", "R3")):
        st.markdown("---")
        st.markdown(
            "**Atenção (informativo):** Para projetos multifamiliares **R2.2** (condomínio horizontal) e **R3** (condomínio vertical), "
            "a legislação menciona uma verificação relacionada à **“quadra máxima” da zona**. "
            "Em caso de dúvida, consulte o licenciamento junto à **SEUMA** e os **anexos da lei**. "
            "*(Referência: **LC 91/2023**, requisito citado para R2.2 e R3.)*"
        )
