from __future__ import annotations
from . import common


def render(ctx):
    common.st.markdown('Se você quiser ver só o essencial deste terreno, este é o resumo principal:')
    resumo_extra = ''
    built = common._num(ctx.get('built_ground'))
    limite = common.practical_ground_limit(ctx)
    if built is not None and built > 0:
        resumo_extra += f"\n- **Área pretendida informada:** {common._fmt_num(built)} m²"
        adotada = limite if (limite is not None and built > limite) else built
        resumo_extra += f"\n- **Área adotada no relatório:** {common._fmt_num(adotada)} m²"
        resumo_extra += "\n- **TO efetiva considerada:** —"
        resumo_extra += "\n- **Área livre remanescente:** —"
        if limite is not None and built > limite:
            resumo_extra += "\n- **Observação:** a área pretendida ultrapassa o limite real do térreo e precisa ser ajustada."
    if limite is not None:
        resumo_extra += f"\n- **Limite real de ocupação no térreo:** {common._fmt_num(limite)} m²"
    if common.is_r21_ctx(ctx):
        resumo_extra += "\n- **Limite tipológico R2.1:** máximo de 2 pavimentos"
    if common.is_zeip9(ctx):
        resumo_extra += "\n- **Atenção ZEIP_9:** não tratar como permissão simples para obra nova/novo edifício sem confirmação do órgão competente"
    common.st.markdown(
        f"- **Uso analisado:** {ctx.get('use_label')}\n"
        f"- **Zona:** {ctx.get('zone') or '—'}\n"
        f"- **Tipo de lote:** {ctx.get('lot_type_label') or '—'}\n"
        f"- **Via:** {ctx.get('via') or '—'}\n"
        f"- **Tipo de via:** {ctx.get('via_tipo_txt') or '—'}\n"
        f"- **Resultado final:** {ctx.get('icon')} **{ctx.get('status_curto')}**\n"
        f"- **TO máxima:** {common._fmt_pct(ctx.get('to_max_pct'))}\n"
        f"- **TP mínima:** {common._fmt_pct(ctx.get('tp_min_pct'))}\n"
        f"- **IA máximo:** {common._fmt_num(ctx.get('ia_max'), 2)}\n"
        f"- **Altura permitida máxima:** {common._fmt_num(ctx.get('gabarito_f'))} m"
        f"{resumo_extra}"
    )
