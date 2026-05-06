from __future__ import annotations
from . import common


def _rule_num(ctx, *keys):
    rule = ctx.get('rule') or {}
    for k in keys:
        v = rule.get(k)
        if v not in (None, ''): return v
    return None

def render(ctx):
    common.st.markdown("Depois de entender se o uso é permitido, o próximo passo é ver as regras básicas da zona para começar o estudo.")
    area_min = _rule_num(ctx, 'area_min_lote_m2','area_lote_min_m2','lote_min_area_m2')
    area_max = _rule_num(ctx, 'area_max_lote_m2','area_lote_max_m2','lote_max_area_m2')
    test_min = _rule_num(ctx, 'testada_min_m','testada_min_meio_m','testada_minima_m')
    test_max = _rule_num(ctx, 'testada_max_m','testada_max_meio_m')
    common.st.markdown(
        f"- **TO máxima:** {common._fmt_pct(ctx['to_max_pct'])}\n"
        f"- **TP mínima:** {common._fmt_pct(ctx['tp_min_pct'])}\n"
        f"- **IA máximo:** {common._fmt_num(ctx['ia_max'], 2)}\n"
        f"- **IA mínimo:** {common._fmt_num(ctx['ia_min'], 2)}\n"
        f"- **Recuo frontal:** {common._fmt_num(ctx['rec_fr'])} m\n"
        f"- **Recuo lateral:** {common._fmt_num(ctx['rec_lat'])} m\n"
        f"- **Recuo de fundos:** {common._fmt_num(ctx['rec_fun'])} m\n"
        f"- **Altura permitida máxima da zona:** {common._fmt_num(ctx['gabarito_f'])} m\n"
        f"- **Área mínima do lote:** {common._fmt_num(area_min)} m²\n"
        f"- **Área máxima do lote:** {common._fmt_num(area_max)} m²\n"
        f"- **Testada mínima:** {common._fmt_num(test_min)} m\n"
        f"- **Testada máxima:** {common._fmt_num(test_max)} m"
    )
    for alerta in common.dimension_alerts(ctx): common.st.warning(alerta)
    if common.is_zeip(ctx): common.st.warning(common.zeip_alert_text())
    if common.is_zeip9(ctx): common.st.warning(common.zeip9_alert_text())
    common.st.markdown('Esses são os parâmetros que mais influenciam o estudo inicial do projeto.')
