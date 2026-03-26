from __future__ import annotations
from . import common

def render(ctx):
    common.st.markdown("Se você quiser ver só o essencial deste terreno, este é o resumo principal:")
    resumo_uso = ctx['uso_label']
    if ctx['multi_tipo'] in ('R22', 'R2.2', 'R2_2') or ctx['use_type_code'].endswith('R22'):
        resumo_uso = 'R2.2 — condomínio horizontal com via interna'
    if ctx['multi_tipo'] in ('R3', 'R03') or ctx['use_type_code'].endswith('R3'):
        resumo_uso = 'R3 — residência multifamiliar vertical'
    resumo_extra = ''
    if ctx['built_ground'] is not None and ctx['a_adotada'] is not None:
        resumo_extra += f"\n- **Área pretendida informada:** {common._fmt_num(ctx['built_ground'])} m²"
        resumo_extra += f"\n- **Área adotada no relatório:** {common._fmt_num(ctx['a_adotada'])} m²"
        if ctx['to_utilizada_pct'] is not None:
            resumo_extra += f"\n- **TO efetiva considerada:** {common._fmt_pct(ctx['to_utilizada_pct'])}"
        if ctx['area_livre_projeto'] is not None:
            resumo_extra += f"\n- **Área livre remanescente:** {common._fmt_num(ctx['area_livre_projeto'])} m²"
        if ctx['ia_saldo'] is not None:
            resumo_extra += f"\n- **Saldo estimado pelo IA:** {common._fmt_num(ctx['ia_saldo'])} m²"
    common.st.markdown(
        f"- **Uso analisado:** {resumo_uso}\n- **Zona:** {ctx['zone_label'] or ctx['zona']}\n- **Tipo de lote:** {ctx['tipo_lote']}\n- **Via:** {ctx['via']}\n- **Tipo de via:** {ctx['via_tipo_txt']}\n- **Resultado final:** {ctx['icon']} {ctx['status_curto']}\n- **TO máxima:** {common._fmt_pct(ctx['to_max_pct'])}\n- **TP mínima:** {common._fmt_pct(ctx['tp_min_pct'])}\n- **IA máximo:** {common._fmt_num(ctx['ia_max'], 2) if ctx['ia_max'] not in (None, '') else '—'}\n- **Altura permitida máxima:** {common._fmt_num(ctx['gabarito_f'])} m{resumo_extra}"
    )
