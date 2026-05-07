from __future__ import annotations
from . import common


def _clean(value, fallback="—"):
    s = str(value or "").strip()
    if not s or s.lower() in {"none", "null", "nan", "—", "-"}:
        return fallback
    return s


def _uso_resumo(ctx: dict) -> str:
    multi_tipo = str(ctx.get("multi_tipo") or "").upper()
    use_type_code = str(ctx.get("use_type_code") or "").upper()
    if multi_tipo in ("R22", "R2.2", "R2_2") or use_type_code.endswith("R22"):
        return "R2.2 — condomínio horizontal com via interna"
    if multi_tipo in ("R3", "R03") or use_type_code.endswith("R3"):
        return "R3 — residência multifamiliar vertical"
    if multi_tipo in ("R21", "R2.1", "R2_1") or use_type_code.endswith("R21"):
        return "R2.1 — 2 unidades no mesmo lote (justapostas ou sobrepostas)"
    return _clean(ctx.get("uso_label"), "residencial multifamiliar")


def _zona_resumo(ctx: dict) -> str:
    zona = _clean(ctx.get("zona"), "")
    subzona = _clean(ctx.get("subzona"), "")
    zone_label = _clean(ctx.get("zone_label"), "")
    if zona and subzona and subzona.upper() not in {"PADRAO", zona.upper()}:
        return f"{zona} — {subzona.replace('_', ' ')}"
    return zone_label or zona or "—"


def _resultado_resumo(ctx: dict) -> str:
    if ctx.get("is_irregular"):
        common.st.markdown(
            "👉 **Observação:** por se tratar de terreno irregular, esse valor é uma referência máxima pela Taxa de Ocupação. "
            "A implantação real depende da geometria do lote e deve ser confirmada em projeto e no licenciamento."
        )

    if ctx.get("is_zeip9"):
        return "⚠️ EXIGE CONFIRMAÇÃO — ZEIP_9"
    if ctx.get("r21_testada_baixa"):
        return "⚠️ PERMITE COM RESSALVA"
    return f"{_clean(ctx.get('icon'), '')} {_clean(ctx.get('status_curto'))}".strip()


def render(ctx):
    common.st.markdown("Se você quiser ver só o essencial deste terreno, este é o resumo principal:")
    resumo_uso = _uso_resumo(ctx)
    zona_txt = _zona_resumo(ctx)
    tipo_lote = "Terreno irregular" if ctx.get("is_irregular") else _clean(ctx.get("tipo_lote"), "Meio de quadra")
    via = _clean(ctx.get("via"))
    via_tipo = _clean(ctx.get("via_tipo_txt"))
    resultado = _resultado_resumo(ctx)

    resumo_extra = ""
    limite_label = "Limite máximo pela Taxa de Ocupação" if ctx.get("is_irregular") else "Limite real de ocupação no térreo"
    if ctx.get('built_ground') is not None and ctx.get('a_adotada') is not None:
        resumo_extra += f"\n- **Área pretendida informada:** {common._fmt_num(ctx['built_ground'])} m²"
        resumo_extra += f"\n- **Área adotada no relatório:** {common._fmt_num(ctx['a_adotada'])} m²"
        if ctx.get('to_utilizada_pct') is not None:
            resumo_extra += f"\n- **TO efetiva considerada:** {common._fmt_pct(ctx['to_utilizada_pct'])}"
        if ctx.get('area_livre_projeto') is not None:
            resumo_extra += f"\n- **Área livre remanescente:** {common._fmt_num(ctx['area_livre_projeto'])} m²"
        if ctx.get('ia_saldo') is not None:
            resumo_extra += f"\n- **Saldo estimado pelo IA:** {common._fmt_num(ctx['ia_saldo'])} m²"
    elif ctx.get('teto_relatorio') is not None:
        resumo_extra += f"\n- **Limite real de ocupação no térreo:** {common._fmt_num(ctx['teto_relatorio'])} m²"

    common.st.markdown(
        f"- **Uso analisado:** {resumo_uso}\n"
        f"- **Zona:** {zona_txt}\n"
        f"- **Tipo de lote:** {tipo_lote}\n"
        f"- **Via:** {via}\n"
        f"- **Tipo de via:** {via_tipo}\n"
        f"- **Resultado final:** {resultado}\n"
        f"- **TO máxima:** {common._fmt_pct(ctx.get('to_max_pct'))}\n"
        f"- **TP mínima:** {common._fmt_pct(ctx.get('tp_min_pct'))}\n"
        f"- **IA máximo:** {common._fmt_num(ctx.get('ia_max'), 2) if ctx.get('ia_max') not in (None, '') else '—'}\n"
        f"- **Altura permitida máxima:** {common._fmt_num(ctx.get('gabarito_f'))} m{resumo_extra}"
    )

    if ctx.get("is_zeip9"):
        common.st.warning(
            "⚠️ **Atenção — ZEIP_9:** a tabela pode indicar adequabilidade, mas este setor possui restrição específica quanto à construção de novos edifícios. "
            "Como R3 é uma tipologia vertical, não trate este resultado como permissão simples para obra nova; confirme a possibilidade no licenciamento municipal e verifique a regra de não alteração da configuração dos lotes existentes."
        )

    if ctx.get("r21_testada_baixa"):
        common.st.warning(
            "⚠️ **Atenção — R2.1:** o uso R2.1 aparece como permitido para esta zona, mas a testada informada é inferior a 8,00 m para R2.1 justaposto fora de ZEIS. "
            "Antes de seguir, revise o enquadramento do projeto ou confirme a possibilidade no licenciamento municipal."
        )
