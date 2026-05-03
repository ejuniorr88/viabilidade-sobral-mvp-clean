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

        common.st.markdown(
            f"- **Por zona:** {ctx['zone_class'] or 'não encontrado'}"
            + (f" ({common._sigla_nome(ctx['zone_class'])})" if ctx["zone_class"] else "")
            + "\n"
            + via_line
            + f"\n- **Resumo final:** {ctx['icon']} **{ctx['status_curto']}**"
        )

        if ctx["status_curto"] in (
            "PERMITE",
            "PERMITE SOMENTE PEQUENO PORTE",
            "PERMITE PEQUENO OU MÉDIO PORTE",
            "PERMITE PELA VIA",
            "PERMITE PELA VIA SOMENTE PEQUENO PORTE",
            "PERMITE PELA VIA PEQUENO OU MÉDIO PORTE",
        ):
            common.st.success(f"{ctx['icon']} **Resumo final: {ctx['status_curto']}.** {ctx['explicacao']}")
        elif ctx["status_curto"] in (
            "DEPENDE DO PORTE",
            "PROJETO ESPECIAL",
            "POSSÍVEL PELA VIA",
            "SEM DADO",
            "POSSÍVEL PELA VIA — PEQUENO PORTE",
            "POSSÍVEL PELA VIA — PEQUENO OU MÉDIO PORTE",
            "PROJETO ESPECIAL PELA VIA",
        ):
            common.st.warning(f"{ctx['icon']} **Resumo final: {ctx['status_curto']}.** {ctx['explicacao']}")
        else:
            common.st.error(f"{ctx['icon']} **Resumo final: {ctx['status_curto']}.** {ctx['explicacao']}")
