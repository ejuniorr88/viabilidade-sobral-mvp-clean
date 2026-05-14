from __future__ import annotations
from . import common

def render(ctx):
    common.st.markdown("**Depois de entender se o uso é permitido, o próximo passo é ver as regras básicas da zona para começar o estudo.**")
    if not ctx["rule"]:
        common.st.warning("Ainda não temos uma regra específica do multifamiliar carregada do Supabase para esta zona. Os próximos limites precisam ser confirmados diretamente no licenciamento e nos anexos da lei.")
    else:
        common.st.markdown(
            f"- **TO máxima:** {common._fmt_pct(ctx['to_max_pct'])}\n"
            f"- **TP mínima:** {common._fmt_pct(ctx['tp_min_pct'])}\n"
            f"- **IA máximo:** {common._fmt_num(ctx['ia_max'], 2) if ctx['ia_max'] not in (None, '') else '—'}\n"
            f"- **IA mínimo:** {common._fmt_num(ctx['ia_min'], 2) if ctx['ia_min'] not in (None, '') else 'não informado'}\n"
            f"- **Recuo frontal:** {common._fmt_num(ctx['rec_fr'])} m\n"
            f"- **Recuo lateral:** {common._fmt_num(ctx['rec_lat'])} m\n"
            f"- **Recuo de fundos:** {common._fmt_num(ctx['rec_fun'])} m\n"
            f"- **Altura permitida máxima da zona:** {common._fmt_num(ctx['gabarito_f'])} m\n"
            f"- **Área mínima do lote:** {common._fmt_num(ctx.get('area_min'))} m²\n"
            f"- **Área máxima do lote:** {common._fmt_num(ctx.get('area_max'))} m²\n"
            f"- **Testada mínima:** {common._fmt_num(ctx.get('testada_min'))} m\n"
            f"- **Testada máxima:** {common._fmt_num(ctx.get('testada_max'))} m"
        )
    try:
        area_min = float(ctx.get('area_min')) if ctx.get('area_min') is not None else None
        area_max = float(ctx.get('area_max')) if ctx.get('area_max') is not None else None
    except Exception:
        area_min = area_max = None

    if area_min is not None and area_max is not None and area_max < area_min:
        common.st.markdown(
            "**Observação especial sobre as dimensões do lote:** nesta zona, a área máxima cadastrada aparece menor que a área mínima. "
            "Em ZEIP ou área patrimonial, isso pode indicar uma regra especial ligada à preservação da configuração dos lotes existentes. "
            "Na prática, não trate essa informação como erro automático nem como autorização para alterar o lote. "
            "Confirme a situação cadastral, a matrícula/documentação do imóvel e a validade do lote existente no licenciamento, principalmente se o imóvel já existir regularmente."
        )

    common.st.markdown("**Esses são os parâmetros que mais influenciam o estudo inicial do projeto.**")
