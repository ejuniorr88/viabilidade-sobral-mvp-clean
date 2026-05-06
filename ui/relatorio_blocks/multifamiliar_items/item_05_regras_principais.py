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
    common.st.markdown("**Esses são os parâmetros que mais influenciam o estudo inicial do projeto.**")
