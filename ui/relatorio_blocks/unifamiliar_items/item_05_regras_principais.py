from __future__ import annotations
import streamlit as st
from .common import md, fmt_pct, fmt_num, dimension_alerts, is_zeip, is_zeip9, zeip_alert_text, zeip9_alert_text


def _rule_num(ctx, *keys):
    rule = ctx.get('rule') or {}
    for k in keys:
        v = rule.get(k)
        if v not in (None, ''): return v
    return None

def render(ctx: dict) -> None:
    area_min = _rule_num(ctx,'area_min_lote_m2','area_lote_min_m2','lote_min_area_m2')
    area_max = _rule_num(ctx,'area_max_lote_m2','area_lote_max_m2','lote_max_area_m2')
    test_min = _rule_num(ctx,'testada_min_m','testada_min_meio_m','testada_minima_m')
    test_max = _rule_num(ctx,'testada_max_m','testada_max_meio_m')
    md("Depois de entender a zona, o próximo passo é ver as regras básicas do lote.\n\nPara este terreno, vale olhar principalmente:\n\n- ocupação máxima no térreo\n- área que precisa ficar livre\n- recuos\n- altura máxima\n- potencial total de construção")
    md(f"**Resumo das regras**\n\n- **TO máxima:** {fmt_pct(ctx.get('to_max'))}\n- **TP mínima:** {fmt_pct(ctx.get('tp_min'))}\n- **IA máximo:** {fmt_num(ctx.get('ia_max'), 2)}\n- **IA mínimo:** {fmt_num(ctx.get('ia_min'), 2)}\n- **Recuos:** Frontal: {fmt_num(ctx.get('rec_fr'))} m | Laterais: {fmt_num(ctx.get('rec_lat'))} m | Fundos: {fmt_num(ctx.get('rec_fun'))} m\n- **Altura máxima:** {fmt_num(ctx.get('gabarito'))} m\n- **Área mínima do lote:** {fmt_num(area_min)} m²\n- **Área máxima do lote:** {fmt_num(area_max)} m²\n- **Testada mínima:** {fmt_num(test_min)} m\n- **Testada máxima:** {fmt_num(test_max)} m")
    for alerta in dimension_alerts(ctx): st.warning(alerta)
    if is_zeip(ctx): st.warning(zeip_alert_text())
    if is_zeip9(ctx): st.warning(zeip9_alert_text())
    md("Essas são as regras que mais impactam o projeto.")
