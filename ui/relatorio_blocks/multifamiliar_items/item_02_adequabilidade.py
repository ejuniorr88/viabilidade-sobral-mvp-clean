from __future__ import annotations
from . import common


def render(ctx):
    common.st.markdown("**Para saber se o uso residencial multifamiliar é viável neste terreno, a análise cruza duas informações principais: as regras de uso e ocupação do solo da zona onde o lote está localizado e a classificação da via de acesso pelo sistema viário. Em alguns casos, o sistema viário pode mudar a leitura da viabilidade, por isso os dois pontos precisam ser verificados juntos.**")
    if not ctx["zone_class"] and not ctx["via_class"]:
        common.st.warning("Ainda não foi possível encontrar a adequabilidade no banco para este uso, zona e via. Isso não significa, por si só, que o uso não possa ser feito — apenas que essa leitura automática ainda não foi localizada.")
        with common.st.expander("🔎 Diagnóstico (para conferência)"):
            common.st.json(ctx["dbg"])
        return
    via_line = (f"- **Por via:** {ctx['via_class']} ({common._sigla_nome(ctx['via_class'])})" if ctx["via_norm"] and ctx["via_class"] else f"- **Por via:** {ctx['via_tipo_txt'] or 'via local'}")
    common.st.markdown(f"- **Por zona:** {ctx['zone_class'] or 'não encontrado'}" + (f" ({common._sigla_nome(ctx['zone_class'])})" if ctx["zone_class"] else "") + "\n" + via_line + f"\n- **Resumo final:** {ctx['icon']} **{ctx['status_curto']}**")
    if common.is_zeip9(ctx):
        common.st.warning(common.zeip9_alert_text())
    if common.is_r21_ctx(ctx):
        front = common._num(ctx.get('frontage_f') or ctx.get('W'))
        if front is not None and front < 8:
            common.st.warning(f"**Atenção R2.1:** a testada informada é de {common.fmt_num(front)} m. Para R2.1 justaposto fora da ZEIS, a referência mínima é 8,00 m. O uso pode aparecer adequado na tabela, mas o enquadramento tipológico exige conferência e possível ajuste do projeto/licenciamento.")
    for alerta in common.dimension_alerts(ctx):
        common.st.warning(alerta)
    if ctx["status_curto"] in ("PERMITE","PERMITE PELA ZONA E PELA VIA","PERMITE SOMENTE PEQUENO PORTE","PERMITE PEQUENO OU MÉDIO PORTE","PERMITE PELA VIA","PERMITE PELA VIA SOMENTE PEQUENO PORTE","PERMITE PELA VIA PEQUENO OU MÉDIO PORTE"):
        common.st.success(f"{ctx['icon']} **{ctx['status_curto']}.** {ctx['explicacao']}")
    elif ctx["status_curto"] in ("DEPENDE DO PORTE","PROJETO ESPECIAL","POSSÍVEL PELA VIA","SEM DADO","POSSÍVEL PELA VIA — PEQUENO PORTE","POSSÍVEL PELA VIA — PEQUENO OU MÉDIO PORTE","PROJETO ESPECIAL PELA VIA"):
        common.st.warning(f"{ctx['icon']} **{ctx['status_curto']}.** {ctx['explicacao']}")
    else:
        common.st.error(f"{ctx['icon']} **{ctx['status_curto']}.** {ctx['explicacao']}")
