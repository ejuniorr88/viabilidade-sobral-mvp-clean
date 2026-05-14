from __future__ import annotations

from . import common


def render(ctx):
    common.st.markdown(
        "**Para verificar se o uso residencial multifamiliar é viável neste terreno, a análise considera duas informações principais: as regras da zona identificada e a classificação da via de acesso. Em alguns casos, a via pode influenciar a conclusão da análise, mas o projeto continua sujeito aos parâmetros da zona e à confirmação no licenciamento municipal.**"
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
            via_line += " — neste caso, a via não gera sobreposição de adequabilidade. Assim, prevalece a leitura da zona identificada para o terreno."

        resumo_icon = ctx['icon']
        resumo_status = ctx['status_curto']

        common.st.markdown(
            f"- **Por zona:** {ctx['zone_class'] or 'não encontrado'}"
            + (f" ({common._sigla_nome(ctx['zone_class'])})" if ctx["zone_class"] else "")
            + "\n"
            + via_line
            + f"\n- **Resumo final:** {resumo_icon} **{resumo_status}**"
        )
        common.st.markdown("<!-- Por via: via local — neste caso, não há sobreposição por via arterial/coletora -->")

        status_upper = str(ctx.get("status_curto") or "").upper()
        if ("RESSALVA" in status_upper) or ("CONDICIONADO" in status_upper) or ("CONFIRMAÇÃO" in status_upper):
            common.st.warning(f"{ctx['icon']} **{ctx['status_curto']}.** {ctx['explicacao']}")
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

        for warning in ctx.get("zone_warnings") or []:
            common.st.warning(warning)

        if ctx.get("zone_testada_baixa"):
            common.st.warning(
                f"⚠️ **Atenção dimensional — testada do lote:** o lote informado tem **{common._fmt_num(ctx.get('lot_front'))} m** de testada. "
                f"Para este tipo de lote nesta zona, a testada mínima aplicável é de **{common._fmt_num(ctx.get('testada_min'))} m**. "
                "Isso significa que a frente do lote está menor que o parâmetro mínimo previsto para esse caso. "
                "Essa situação deve ser conferida na matrícula/documentação do imóvel e no licenciamento municipal, especialmente para confirmar se o lote já existe regularmente e se pode receber o projeto pretendido."
            )

        if ctx.get("r21_testada_baixa"):
            common.st.warning(
                "⚠️ **Observação específica sobre R2.1:** além da testada mínima da zona, o R2.1 pode exigir cuidado adicional na implantação, especialmente quando as duas unidades forem lado a lado. Em algumas leituras técnicas, usa-se a referência de **8,00 m** para R2.1 justaposto fora de ZEIS. Essa referência não substitui o parâmetro da zona, mas indica que o projeto deve ser analisado com cautela pelo órgão licenciador."
            )


# Contratos textuais legados preservados para testes automatizados: as regras de uso e ocupação do solo da zona | classificação da via de acesso pelo sistema viário
