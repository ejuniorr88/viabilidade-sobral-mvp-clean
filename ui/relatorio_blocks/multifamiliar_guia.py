from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st


def render_multifamiliar_guia(*, calc: Dict[str, Any], rule: Optional[Dict[str, Any]] = None) -> None:
    """Fase 1 — Guia do Projetista (Multifamiliar).

    - Não calcula número final de unidades/áreas.
    - Não muda layout do app: apenas renderiza o bloco do relatório quando selecionado.
    """

    multi_tipo = (calc.get("multi_tipo") or "").upper()
    use_type_code = (calc.get("use_type_code") or "").upper()

    # Cabeçalho
    st.subheader("Multifamiliar — Fase 1 (Guia do Projetista)")
    st.caption("Guia rápido para iniciar o projeto — sem cálculo final de unidades/áreas. (LC 91/2023 e LC 90/2023)")

    # A) Adequabilidade (placeholder por enquanto)
    st.markdown("### A) Pode / não pode (adequabilidade)")
    st.info(
        "Adequabilidade ainda não cadastrada para multifamiliar (Quadro 2A/2B e Quadro I). "
        "Assim que for cadastrada no Supabase, o sistema passará a exibir A/I/AP/AM/PE automaticamente."
    )

    # B) Parâmetros urbanísticos (se houver regra no Supabase)
    st.markdown("### B) Parâmetros urbanísticos (para começar projeto)")
    if not rule:
        st.warning(
            "Regra urbanística específica do multifamiliar ainda não foi cadastrada no Supabase para esta zona.

"
            "➡️ Você já pode iniciar o estudo, mas **confirme TO/TP/IA/recuos/gabarito** no licenciamento junto à **SEUMA** e nos **anexos da lei**."
        )
    else:
        # Mostra alguns campos básicos se existirem (sem inventar)
        def _pct(v):
            if v is None:
                return None
            try:
                v = float(v)
            except Exception:
                return None
            return v * 100 if v <= 1 else v

        to_max = _pct(rule.get("to_max") if isinstance(rule, dict) else None) or _pct(rule.get("to_max_pct"))
        tp_min = _pct(rule.get("tp_min") if isinstance(rule, dict) else None) or _pct(rule.get("tp_min_pct"))
        ia_max = rule.get("ia_max")

        cols = st.columns(3)
        cols[0].metric("TO máxima", f"{to_max:.0f}%" if isinstance(to_max, (int, float)) else "—")
        cols[1].metric("TP mínima", f"{tp_min:.0f}%" if isinstance(tp_min, (int, float)) else "—")
        cols[2].metric("IA máximo", f"{ia_max}" if ia_max not in (None, "") else "—")

        st.caption("Observação: demais recuos/gabarito/testadas seguem a regra carregada do Supabase para esta zona.")

    # C) Checklist (bem leigo)
    st.markdown("### C) Checklist do tipo escolhido (sem exigir projeto pronto)")

    if multi_tipo in ("R21", "R2.1", "R2_1") or use_type_code.endswith("R21"):
        st.markdown("**R2.1 — 2 unidades no mesmo lote (justapostas ou sobrepostas)**")
        st.markdown(
            "- ✅ **Altura/andares:** pode ter **no máximo 2 pavimentos** (ex.: térreo + 1º andar).
"
            "  *(LC 91/2023 — definição de R2.1)*
"
            "- ✅ **Se for “lado a lado” (justapostas):** a **testada** (frente do lote) deve ter **pelo menos 8,00 m**.
"
            "  *(exceto ZEIS — LC 91/2023, requisito citado para R2.1)*
"
            "- ✅ **Regras urbanísticas (TO/TP/IA/recuos/gabarito):** quando a zona permitir, pode usar os **parâmetros do unifamiliar**,
"
            "  sempre respeitando a **adequabilidade** do uso na zona.
"
            "  *(LC 91/2023 — Art. 106)*"
        )
    elif multi_tipo in ("R22", "R2.2", "R2_2") or use_type_code.endswith("R22"):
        st.markdown("**R2.2 — Condomínio horizontal (via interna)**")
        st.markdown(
            "- ✅ **Acesso de veículos:** abertura mínima **4,00 m** de largura e **4,50 m** de altura livre.
"
            "- ✅ **Via interna:** largura mínima **6,00 m** (referência normativa citada para bombeiros).
"
            "- ✅ **Muro frontal:** pelo menos **25% em gradil/visibilidade**.
"
            "- ✅ **Resíduos:** local de resíduos no alinhamento com abertura para o logradouro.
"
            "- ✅ **Áreas comuns:** acessibilidade + sanitários/copa funcionários + DML.
"
            "- ⚠️ **Lazer:** se passar de 10 unidades, prever lazer mínimo conforme lei.
"
            "*(LC 90/2023 — Art. 168)*"
        )
    elif multi_tipo in ("R3", "R03") or use_type_code.endswith("R3"):
        st.markdown("**R3 — Condomínio vertical (edifício)**")
        st.markdown(
            "- ✅ **Muro frontal:** pelo menos **50% em gradil/visibilidade**.
"
            "- ✅ **Resíduos:** local de resíduos no alinhamento com abertura para o logradouro.
"
            "- ✅ **Áreas comuns:** acessibilidade + sanitários/copa + DML.
"
            "- ⚠️ **Lazer:** prever lazer mínimo conforme lei.
"
            "- ⚠️ **Entregas/recepção:** se passar de 30 unidades, prever espaço mínimo.
"
            "- ⚠️ **EIV:** se passar de 100 unidades, EIV pode ser exigido.
"
            "*(LC 90/2023 — Art. 170; LC 91/2023 — Art. 88)*"
        )
    else:
        st.info("Selecione o tipo de multifamiliar (R2.1 / R2.2 / R3) no Item 2 para exibir o checklist.")

    # D) Vagas (bem leigo, sem falar de Fase 2)
    st.markdown("### D) Vagas de estacionamento (como calcular)")

    st.markdown(
        "A quantidade de vagas depende do **tamanho do apartamento (área construída da unidade)**:

"
        "- 🚗 **Apartamento com menos de 90 m²** → **1 vaga por unidade**
"
        "- 🚗 **Apartamento com 90 m² ou mais** → **1,5 vaga por unidade**

"
        "📌 Na prática, quando aparece **1,5**, o total final deve ser **arredondado para cima** "
        "(porque não existe “meia vaga”).

"
        "*(LC 90/2023 — Anexo IV)*"
    )

    st.markdown("**Exemplo rápido (só para entender a lógica):**")
    st.markdown(
        "- 10 apartamentos com **80 m²** → **10 vagas**
"
        "- 11 apartamentos com **100 m²** → 11 × 1,5 = 16,5 → **17 vagas** (arredonda pra cima)"
    )

    # Aviso informativo da "quadra máxima" (apenas informativo)
    if multi_tipo in ("R22", "R2.2", "R2_2", "R3", "R03") or use_type_code.endswith(("R22", "R3")):
        st.markdown("---")
        st.markdown(
            "**Atenção (informativo):** Para projetos multifamiliares **R2.2** (condomínio horizontal) e **R3** (condomínio vertical), "
            "a legislação menciona uma verificação relacionada à **“quadra máxima” da zona**. "
            "Em caso de dúvida, consulte o licenciamento junto à **SEUMA** e os **anexos da lei**. "
            "*(Referência: **LC 91/2023**, requisito citado para R2.2 e R3.)*"
        )
