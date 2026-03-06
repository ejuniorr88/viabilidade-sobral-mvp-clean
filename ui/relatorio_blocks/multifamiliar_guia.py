from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st


def render_multifamiliar_guia(*, calc: Dict[str, Any], rule: Optional[Dict[str, Any]] = None, **_: Any) -> None:
    """Multifamiliar — Fase 1 (Guia do Projetista).

    Observação: este bloco é apenas informativo (guia). Não calcula número final de unidades/áreas.
    """

    multi_tipo = (calc.get("multi_tipo") or "").upper()
    use_type_code = (calc.get("use_type_code") or "").upper()

    st.subheader("Multifamiliar — Fase 1 (Guia do Projetista)")
    st.caption("Guia rápido para iniciar o projeto — sem cálculo final de unidades/áreas. (LC 91/2023 e LC 90/2023)")

    # A) Adequabilidade
    st.markdown("### A) Pode / não pode (adequabilidade)")
    st.info(
        "Adequabilidade ainda não cadastrada para multifamiliar (Quadro 2A/2B e Quadro I). "
        "Assim que for cadastrada no Supabase, o sistema passará a exibir A/I/AP/AM/PE automaticamente."
    )

    # B) Parâmetros urbanísticos
    st.markdown("### B) Parâmetros urbanísticos (para começar projeto)")
    if not rule:
        st.warning(
            "Regra urbanística específica do multifamiliar ainda não foi cadastrada no Supabase para esta zona.\n\n"
            "➡️ Você já pode iniciar o estudo, mas **confirme TO/TP/IA/recuos/gabarito** no licenciamento junto à **SEUMA** e nos **anexos da lei**."
        )
    else:
        # mostrar apenas se existir, sem inventar
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

    # C) Checklist
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

    # D) Vagas
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
