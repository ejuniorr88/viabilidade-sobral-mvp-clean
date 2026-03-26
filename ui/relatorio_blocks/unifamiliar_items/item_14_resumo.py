from __future__ import annotations

from .common import md, fmt_num, fmt_pct


def render(ctx: dict) -> None:
    md("**Se você quiser ver só o essencial deste terreno, este é o resumo principal:**")
    resumo_extra = ""
    if ctx['area_pedida'] is not None and ctx['A_considerada'] is not None:
        resumo_extra += f"\n- **Área pretendida informada:** {fmt_num(ctx['area_pedida'])} m²"
        resumo_extra += f"\n- **Área adotada no relatório:** {fmt_num(ctx['A_considerada'])} m²"
        if ctx['to_projeto_pct'] is not None:
            resumo_extra += f"\n- **TO efetiva considerada:** {fmt_pct(ctx['to_projeto_pct'])}"
        if ctx['A_livre'] is not None:
            resumo_extra += f"\n- **Área livre remanescente:** {fmt_num(ctx['A_livre'])} m²"
        if ctx['A_ia_saldo'] is not None:
            resumo_extra += f"\n- **Saldo estimado pelo IA:** {fmt_num(ctx['A_ia_saldo'])} m²"
    md(
        f"- **Uso analisado:** {ctx['uso_label']}\n"
        f"- **Zona:** {ctx['zone_title']}\n"
        f"- **Tipo de lote:** {ctx['tipo_lote']}\n"
        f"- **Via:** {ctx['via']}\n"
        f"- **Tipo de via:** {ctx['via_tipo']}\n\n"
        f"- **TO máxima:** {fmt_pct(ctx['to_max'])}\n"
        f"- **TP mínima:** {fmt_pct(ctx['tp_min'])}\n"
        f"- **IA máximo:** {fmt_num(ctx['ia_max']) if ctx['ia_max'] is not None else '—'}\n"
        f"- **Altura máxima:** {fmt_num(ctx['gabarito_m'])} m\n\n"
        f"- **Área máxima no térreo pela TO:** {fmt_num(ctx['A_to'])} m²\n"
        f"- **Área permeável mínima:** {fmt_num(ctx['A_perm_min'])} m²\n"
        f"- **Área total máxima estimada:** {fmt_num(ctx['A_total'])} m²"
        f"{resumo_extra}"
    )
    if ctx['area_pedida'] is not None and ctx['A_considerada'] is not None:
        if ctx['excedeu_area']:
            md(
                f"👉 **Em resumo:** você informou **{fmt_num(ctx['area_pedida'])} m²** no térreo, mas o relatório adotou **{fmt_num(ctx['A_considerada'])} m²** para respeitar os limites urbanísticos do lote. "
                f"Com isso, a TO considerada ficou em **{fmt_pct(ctx['to_projeto_pct'])}**, a área livre remanescente em **{fmt_num(ctx['A_livre'])} m²** e o saldo estimado pelo IA em **{fmt_num(ctx['A_ia_saldo'])} m²**."
            )
        else:
            md(
                f"👉 **Em resumo:** o relatório considerou a área pretendida de **{fmt_num(ctx['A_considerada'])} m²** no térreo. "
                f"Com isso, a TO considerada ficou em **{fmt_pct(ctx['to_projeto_pct'])}**, a área livre remanescente em **{fmt_num(ctx['A_livre'])} m²** e o saldo estimado pelo IA em **{fmt_num(ctx['A_ia_saldo'])} m²**."
            )
    else:
        md(
            f"👉 **Em resumo:** você pode ocupar até **{fmt_pct(ctx['to_max'])}** do lote no térreo; "
            f"precisa manter pelo menos **{fmt_pct(ctx['tp_min'])}** do terreno permeável; "
            f"a construção pode chegar até **{fmt_num(ctx['ia_max']) if ctx['ia_max'] is not None else '—'}** vezes a área do lote no total; "
            "e a altura deve respeitar o limite da zona."
        )
