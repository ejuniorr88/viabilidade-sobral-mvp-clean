from __future__ import annotations

from . import common


def render(ctx):
    common.st.markdown(
        "**Para saber se o uso residencial multifamiliar é viável neste terreno, a análise cruza duas informações principais: as regras de uso e ocupação do solo da zona onde o lote está localizado e a classificação da via de acesso pelo sistema viário. Em alguns casos, o sistema viário pode mudar a leitura da viabilidade, por isso os dois pontos precisam ser verificados juntos.**"
    )

    if not ctx["zone_class"] and not ctx["via_class"]:
        common.st.warning(
            "Ainda não foi possível encontrar a adequabilidade no banco para este uso, zona e via. Isso não significa, por si só, que o uso não possa ser feito — apenas que essa leitura automática ainda não foi localizada."
        )
        with common.st.expander("🔎 Diagnóstico (para conferência)"):
            common.st.json(ctx["dbg"])
    else:
        via_line = (
            f"- **Por via:** {ctx['via_class']} ({common._sigla_nome(ctx['via_class'])})"
            if ctx["via_norm"] and ctx["via_class"]
            else f"- **Por via:** {ctx['via_tipo_txt'] or 'via local'}"
        )
        if (not ctx["via_norm"] or not ctx["via_class"]) and "local" in str(ctx.get("via_tipo_txt") or "via local").lower():
            via_line += " — neste caso, não há sobreposição por via arterial/coletora."

        resumo_icon = ctx['icon']
        resumo_status = ctx['status_curto']
        if ctx.get("is_zeip9"):
            resumo_icon = "⚠️"
            resumo_status = "EXIGE CONFIRMAÇÃO — ZEIP_9"
        elif ctx.get("r21_testada_baixa"):
            resumo_icon = "⚠️"
            resumo_status = "PERMITE COM RESSALVA — R2.1"

        common.st.markdown(
            f"- **Por zona:** {ctx['zone_class'] or 'não encontrado'}"
            + (f" ({common._sigla_nome(ctx['zone_class'])})" if ctx["zone_class"] else "")
            + "\n"
            + via_line
            + f"\n- **Resumo final:** {resumo_icon} **{resumo_status}**"
        )

        if ctx.get("is_zeip9"):
            # O resumo acima já troca o selo final para "EXIGE CONFIRMAÇÃO".
            # A orientação completa da ZEIP_9 é exibida abaixo, uma única vez,
            # para evitar duplicidade visual no relatório.
            pass
        elif ctx["status_curto"] in (
            "PERMITE",
            "PERMITE PELA ZONA E PELA VIA",
            "PERMITE SOMENTE PEQUENO PORTE",
            "PERMITE PEQUENO OU MÉDIO PORTE",
            "PERMITE PELA VIA",
            "PERMITE PELA VIA SOMENTE PEQUENO PORTE",
            "PERMITE PELA VIA PEQUENO OU MÉDIO PORTE",
        ):
            common.st.success(f"{ctx['icon']} **{ctx['status_curto']}.** {ctx['explicacao']}")
        elif ctx["status_curto"] in (
            "DEPENDE DO PORTE",
            "PROJETO ESPECIAL",
            "POSSÍVEL PELA VIA",
            "SEM DADO",
            "POSSÍVEL PELA VIA — PEQUENO PORTE",
            "POSSÍVEL PELA VIA — PEQUENO OU MÉDIO PORTE",
            "PROJETO ESPECIAL PELA VIA",
        ):
            common.st.warning(f"{ctx['icon']} **{ctx['status_curto']}.** {ctx['explicacao']}")
        else:
            common.st.error(f"{ctx['icon']} **{ctx['status_curto']}.** {ctx['explicacao']}")

        if ctx.get("is_zeip9"):
            common.st.warning(
                "⚠️ **Atenção especial — ZEIP_9:** embora a tabela de adequabilidade possa indicar o uso como adequado, este setor possui restrição específica quanto à construção de novos edifícios. Para R3 ou obra nova, não trate esta conclusão como permissão simples; confirme se o caso é obra nova, reforma, regularização, ampliação ou intervenção em edificação existente junto ao órgão competente. Também deve ser verificada a regra de não alteração da configuração dos lotes existentes."
            )

        if ctx.get("r21_testada_baixa"):
            common.st.warning(
                "⚠️ **Atenção — R2.1 com testada inferior a 8,00 m:** o uso R2.1 aparece como adequado para esta zona, mas a testada informada é menor que a referência usual de 8,00 m para R2.1 justaposto fora de ZEIS. Esse caso não deve ser tratado como liberação automática nem como impedimento automático: exige análise no licenciamento municipal. O interessado deve comprovar a situação real do lote e das edificações vizinhas, inclusive por documentação do imóvel/escritura pública quando necessário, especialmente quando a justificativa depender da existência de vizinhos ou construções nos dois lados."
            )
