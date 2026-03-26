from __future__ import annotations

from .common import md


def render(ctx: dict) -> None:
    st = ctx["st"]
    md("**Depois de entender se o uso é permitido, o próximo passo é ver as regras básicas da zona para começar o estudo.**")
    if not ctx['rule']:
        st.warning("Ainda não temos uma regra específica do multifamiliar carregada do Supabase para esta zona. Os próximos limites precisam ser confirmados diretamente no licenciamento e nos anexos da lei.")
    else:
        md(
            f"- **TO máxima:** {ctx['_fmt_pct'](ctx['to_max_pct'])}\n"
            f"- **TP mínima:** {ctx['_fmt_pct'](ctx['tp_min_pct'])}\n"
            f"- **IA máximo:** {ctx['_fmt_num'](ctx['ia_max'], 2) if ctx['ia_max'] not in (None, '') else '—'}\n"
            f"- **IA mínimo:** {ctx['_fmt_num'](ctx['ia_min'], 2) if ctx['ia_min'] not in (None, '') else 'não informado'}\n"
            f"- **Recuo frontal:** {ctx['_fmt_num'](ctx['rec_fr'])} m\n"
            f"- **Recuo lateral:** {ctx['_fmt_num'](ctx['rec_lat'])} m\n"
            f"- **Recuo de fundos:** {ctx['_fmt_num'](ctx['rec_fun'])} m\n"
            f"- **Altura permitida máxima da zona:** {ctx['_fmt_num'](ctx['gabarito_f'])} m\n"
            f"- **Área mínima do lote:** {ctx['_fmt_num'](ctx['area_min'])} m²\n"
            f"- **Testada mínima:** {ctx['_fmt_num'](ctx['testada_min'])} m"
        )
    md("**Esses são os parâmetros que mais influenciam o estudo inicial do projeto.**")
