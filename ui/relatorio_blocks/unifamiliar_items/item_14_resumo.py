from __future__ import annotations
from .common import md, fmt_num, fmt_pct, practical_ground_limit, is_zeip9


def render(ctx: dict) -> None:
    md('Se você quiser ver só o essencial deste terreno, este é o resumo principal:')
    limite = practical_ground_limit(ctx)
    extra = ''
    if ctx.get('area_pedida') is not None:
        extra += f"\n- **Área pretendida informada:** {fmt_num(ctx.get('area_pedida'))} m²"
        extra += f"\n- **Área adotada no relatório:** {fmt_num(ctx.get('A_considerada'))} m²"
        extra += f"\n- **TO considerada:** {fmt_pct(ctx.get('to_efetiva'))}"
        extra += f"\n- **Área livre remanescente:** {fmt_num(ctx.get('A_livre'))} m²"
        extra += f"\n- **Saldo estimado pelo IA:** {fmt_num(ctx.get('saldo_ia'))} m²"
    if limite is not None:
        extra += f"\n- **Limite real de ocupação no térreo:** {fmt_num(limite)} m²"
    if is_zeip9(ctx):
        extra += "\n- **Atenção ZEIP_9:** não tratar como permissão simples para obra nova/novo edifício sem confirmação do órgão competente"
    md(f"- **Uso analisado:** residência unifamiliar\n- **Zona:** {ctx.get('zone_title') or ctx.get('zone') or '—'}\n- **Tipo de lote:** {ctx.get('lot_type_label') or '—'}\n- **Via:** {ctx.get('via') or '—'}\n- **Tipo de via:** {ctx.get('via_tipo') or '—'}\n- **TO máxima:** {fmt_pct(ctx.get('to_max'))}\n- **TP mínima:** {fmt_pct(ctx.get('tp_min'))}\n- **IA máximo:** {fmt_num(ctx.get('ia_max'), 2)}\n- **Altura máxima:** {fmt_num(ctx.get('gabarito'))} m\n- **Área máxima no térreo pela TO:** {fmt_num(ctx.get('A_to'))} m²\n- **Área permeável mínima:** {fmt_num(ctx.get('A_perm_min'))} m²\n- **Área total máxima estimada:** {fmt_num(ctx.get('A_ia_max'))} m²{extra}\n\n👉 **Em resumo:** você pode ocupar até **{fmt_num(ctx.get('A_to'))} m²** no térreo, precisa manter pelo menos **{fmt_num(ctx.get('A_perm_min'))} m²** permeáveis e respeitar os demais parâmetros urbanísticos.")
# contrato: área livre remanescente
