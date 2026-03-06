from __future__ import annotations

from typing import Any, Dict

import streamlit as st


def _fmt_num(v: Any, dec: int = 2) -> str:
    try:
        if v is None:
            return "—"
        f = float(v)
        return f"{f:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "—"


def _fmt_pct(v: Any, dec: int = 1) -> str:
    try:
        if v is None:
            return "—"
        f = float(v)
        return f"{f:.{dec}f}%"
    except Exception:
        return "—"


def _to_pct(rule: Dict[str, Any], key_pct: str, key_frac: str) -> float | None:
    v = rule.get(key_pct, None)
    if v is not None:
        try:
            return float(v)
        except Exception:
            pass
    v = rule.get(key_frac, None)
    if v is None:
        return None
    try:
        f = float(v)
        return f * 100.0 if 0 <= f <= 1.0 else f
    except Exception:
        return None


def render_multifamiliar_guia(*, calc: Dict[str, Any], rule: Dict[str, Any], is_irregular: bool) -> None:
    """FASE 1 — Guia do Projetista (Multifamiliar).

    Mostra:
    - Adequabilidade (se existir no banco; senão, pendente)
    - Parâmetros urbanísticos (TO/TP/IA/recuos/gabarito)
    - Checklist por tipo (R2.1 / R2.2 / R3)
    - Vagas (regra de cálculo, sem fechar número final)
    """

    tipo = (calc.get("multi_tipo") or "").upper()  # "R2.1", "R2.2", "R3"
    zone = calc.get("zone") or calc.get("zone_sigla") or "—"
    via_tipo = calc.get("via_tipo") or calc.get("street_type") or "—"

    A = float(calc.get("lot_area_m2") or 0.0)

    st.markdown("### Multifamiliar — Fase 1 (Guia do Projetista)")
    st.caption("Guia rápido para iniciar o projeto — sem cálculo final de unidades/áreas. (LC 91/2023 e LC 90/2023)")

    # -------------------------
    # A) Adequabilidade (placeholder)
    # -------------------------
    st.markdown("#### A) Pode / não pode (adequabilidade)")
    # Se futuramente você cadastrar adequabilidade no Supabase, preencha aqui via calc["adequab_status"] etc.
    adeq = calc.get("adequabilidade") or calc.get("adequab") or None
    if adeq:
        st.success(f"Classificação: **{adeq}**")
    else:
        st.info(
            "Adequabilidade **ainda não cadastrada** para multifamiliar (Quadro 2A/2B e Quadro I). "
            "Assim que for cadastrada no Supabase, o sistema passará a exibir **A/I/AP/AM/PE** automaticamente."
        )

    # -------------------------
    # B) Parâmetros urbanísticos
    # -------------------------
    st.markdown("#### B) Parâmetros urbanísticos (para começar projeto)")
    to_max = _to_pct(rule, "to_max_pct", "to_max")
    tp_min = _to_pct(rule, "tp_min_pct", "tp_min")
    ia_max = rule.get("ia_max")
    rec_fr = rule.get("recuo_frontal_m")
    rec_lat = rule.get("recuo_lateral_m")
    rec_fun = rule.get("recuo_fundos_m")
    gabarito_m = rule.get("gabarito_m")
    gabarito_pav = rule.get("gabarito_pav")

    if not isinstance(rule, dict) or not rule:
        st.warning(
            "Regra urbanística específica do multifamiliar **ainda não foi cadastrada** no Supabase para esta zona.\n\n"
            "➡️ Você pode iniciar o estudo, mas confirme TO/TP/IA/recuos/gabarito na SEUMA/anexos da lei."
        )
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("TO máxima", _fmt_pct(to_max))
            if to_max is not None and A > 0:
                st.caption(f"Máx. no térreo: {_fmt_num(A * (to_max/100.0))} m²")
        with c2:
            st.metric("TP mínima", _fmt_pct(tp_min))
            if tp_min is not None and A > 0:
                st.caption(f"Mín. permeável: {_fmt_num(A * (tp_min/100.0))} m²")
        with c3:
            st.metric("IA máximo", _fmt_num(ia_max, 2))
            if ia_max is not None and A > 0:
                try:
                    st.caption(f"Máx. área total (IA×área): {_fmt_num(A * float(ia_max))} m²")
                except Exception:
                    pass

        st.markdown(
            f"""- **Recuo frontal:** {_fmt_num(rec_fr, 2)} m  
- **Recuo lateral:** {_fmt_num(rec_lat, 2)} m  
- **Recuo de fundos:** {_fmt_num(rec_fun, 2)} m  
- **Gabarito:** {_fmt_num(gabarito_m, 2)} m / {_fmt_num(gabarito_pav, 0)} pavimentos
"""
        )

        if is_irregular:
            st.info(
                "ℹ️ Como o lote foi marcado como **terreno irregular**, a implantação por recuos **não é calculada**. "
                "Os limites exibidos aqui servem como referência inicial; a implantação final pode ser reduzida por recuos/forma/licenciamento."
            )

    # -------------------------
    # C) Checklist por tipo
    # -------------------------
    st.markdown("#### C) Checklist do tipo escolhido (sem exigir projeto pronto)")

    if tipo in ("R2.1", "R21", "R2_1"):
        st.markdown(
            """**R2.1 — 2 unidades no mesmo lote (justapostas ou sobrepostas)**  
- **Máximo 2 pavimentos**. *(LC 91/2023 — definição de R2.1)*  
- Para unidades **justapostas**, **testada mínima 8,00 m** (exceto ZEIS). *(LC 91/2023 — requisito citado para R2.1)*  
- Pode usar **parâmetros do unifamiliar** da zona (quando aplicável), respeitando adequabilidade. *(LC 91/2023 — Art. 106)*  
"""
        )
    elif tipo in ("R2.2", "R22", "R2_2"):
        st.markdown(
            """**R2.2 — Condomínio horizontal (via interna)**  
- Acesso às unidades ocorre por **via interna** (não há acesso direto da unidade pela via pública). *(LC 91/2023 — definição de R2.2)*  
- **Abertura para veículos:** 4,00 m (largura) e 4,5 m (altura livre). *(LC 90/2023 — Art. 168)*  
- **Via interna:** 6,00 m (referência bombeiros). *(LC 90/2023 — Art. 168)*  
- **Pavimentação** da via interna (preferencial intertravado). *(LC 90/2023 — Art. 168)*  
- Se **> 10 unidades**, prever **lazer mínimo 5%** da área do empreendimento. *(LC 90/2023 — Art. 168)*  
- **Acessibilidade** em áreas comuns; sanitários + copa funcionários + DML. *(LC 90/2023 — Art. 168)*  
- **25% do muro frontal em gradil/visibilidade.** *(LC 90/2023 — Art. 168)*  
- **Local de resíduos no alinhamento** com abertura para o logradouro. *(LC 90/2023 — Art. 168; Art. 80)*  
- Condomínio: estatuto + CNPJ, ou único proprietário. Habite-se condicionado à conclusão das áreas comuns. *(LC 90/2023 — Art. 168)*  
"""
        )
        st.markdown(
            """**Atenção (informativo):** Para projetos multifamiliares R2.2 (condomínio horizontal) e R3 (condomínio vertical), a legislação menciona uma verificação relacionada à “quadra máxima” da zona. Em caso de dúvida, consulte o licenciamento junto à SEUMA e os anexos da lei. *(Referência: LC 91/2023, requisito citado para R2.2 e R3.)*"""
        )
    else:
        # default R3
        st.markdown(
            f"""**R3 — Multifamiliar vertical (edifício/condomínio vertical)**  
- **Acessibilidade** em áreas comuns; sanitários + copa + DML. *(LC 90/2023 — Art. 170)*  
- **Lazer mínimo:** 5% da área total construída das unidades. *(LC 90/2023 — Art. 170)*  
- **50% do muro frontal em gradil/visibilidade** (pode haver comutação por fachada ativa em via arterial/coletora, com condições). *(LC 90/2023 — Art. 170; LC 91/2023 — Art. 89)*  
- **Local de resíduos no alinhamento** com abertura para o logradouro. *(LC 90/2023 — Art. 170; Art. 80)*  
- Se **> 30 unidades**, prever **espaço de recepção/entregas ≥ 5 m²**. *(LC 90/2023 — Art. 170)*  
- Se **> 100 unidades**, **EIV obrigatório**. *(LC 91/2023 — Art. 88)*  
"""
        )
        st.markdown(
            """**Atenção (informativo):** Para projetos multifamiliares R2.2 (condomínio horizontal) e R3 (condomínio vertical), a legislação menciona uma verificação relacionada à “quadra máxima” da zona. Em caso de dúvida, consulte o licenciamento junto à SEUMA e os anexos da lei. *(Referência: LC 91/2023, requisito citado para R2.2 e R3.)*"""
        )

    # D) Vagas (apenas regra)
    st.markdown("#### D) Vagas de estacionamento (como calcular)")
    st.markdown(
        """A quantidade de vagas depende do **tamanho do apartamento**:

- **Apartamento com menos de 90 m²** → **1 vaga por unidade**
- **Apartamento com 90 m² ou mais** → **1,5 vaga por unidade**  
  *(na prática, o total final deve ser **arredondado para cima**)*

*(LC 90/2023 — Anexo IV)*

**Exemplo rápido:**  
- 10 apartamentos com **80 m²** → **10 vagas**  
- 11 apartamentos com **100 m²** → 11 × 1,5 = 16,5 → **17 vagas** (arredonda pra cima)
"""
    )

    st.divider()
