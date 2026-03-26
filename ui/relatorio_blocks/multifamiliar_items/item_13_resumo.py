from __future__ import annotations

from .common import md


def render(ctx: dict) -> None:
    md("Se você quiser ver só o essencial deste terreno, este é o resumo principal:")
    resumo_extra = ""
    if ctx['built_ground'] is not None and ctx['a_adotada'] is not None:
        resumo_extra += f"\n- **Área pretendida informada:** {ctx['_fmt_num'](ctx['built_ground'])} m²"
        resumo_extra += f"\n- **Área adotada no relatório:** {ctx['_fmt_num'](ctx['a_adotada'])} m²"
        if ctx['to_utilizada_pct'] is not None:
            resumo_extra += f"\n- **TO efetiva considerada:** {ctx['_fmt_pct'](ctx['to_utilizada_pct'])}"
        if ctx['area_livre_projeto'] is not None:
            resumo_extra += f"\n- **Área livre remanescente:** {ctx['_fmt_num'](ctx['area_livre_projeto'])} m²"
        if ctx['ia_saldo'] is not None:
            resumo_extra += f"\n- **Saldo estimado pelo IA:** {ctx['_fmt_num'](ctx['ia_saldo'])} m²"
    md(
        f"- **Uso analisado:** {ctx['resumo_uso']}\n"
        f"- **Zona:** {ctx['zone_label'] or ctx['zona']}\n"
        f"- **Tipo de lote:** {ctx['tipo_lote']}\n"
        f"- **Via:** {ctx['via']}\n"
        f"- **Tipo de via:** {ctx['via_tipo_txt']}\n"
        f"- **Resultado final:** {ctx['icon']} {ctx['status_curto']}\n"
        f"- **TO máxima:** {ctx['_fmt_pct'](ctx['to_max_pct'])}\n"
        f"- **TP mínima:** {ctx['_fmt_pct'](ctx['tp_min_pct'])}\n"
        f"- **IA máximo:** {ctx['_fmt_num'](ctx['ia_max'], 2) if ctx['ia_max'] not in (None, '') else '—'}\n"
        f"- **Altura permitida máxima:** {ctx['_fmt_num'](ctx['gabarito_f'])} m"
        f"{resumo_extra}"
    )
    if ctx['built_ground'] is not None and ctx['a_adotada'] is not None:
        if ctx['built_ground'] > ctx['a_adotada']:
            md(
                f"👉 **Em resumo:** o uso residencial multifamiliar **{ctx['tipo_sigla']}** foi considerado **{ctx['status_curto'].lower()}** neste terreno. "
                f"Você informou **{ctx['_fmt_num'](ctx['built_ground'])} m²** no térreo, mas o relatório adotou **{ctx['_fmt_num'](ctx['a_adotada'])} m²** para respeitar os limites urbanísticos deste cenário. "
                f"Com isso, a TO considerada ficou em **{ctx['_fmt_pct'](ctx['to_utilizada_pct'])}**, a área livre remanescente em **{ctx['_fmt_num'](ctx['area_livre_projeto'])} m²** e o saldo estimado pelo IA em **{ctx['_fmt_num'](ctx['ia_saldo'])} m²**."
            )
        else:
            md(
                f"👉 **Em resumo:** o uso residencial multifamiliar **{ctx['tipo_sigla']}** foi considerado **{ctx['status_curto'].lower()}** neste terreno. "
                f"O relatório considerou a área pretendida de **{ctx['_fmt_num'](ctx['a_adotada'])} m²** no térreo, com TO efetiva de **{ctx['_fmt_pct'](ctx['to_utilizada_pct'])}**, "
                f"área livre remanescente de **{ctx['_fmt_num'](ctx['area_livre_projeto'])} m²** e saldo estimado pelo IA de **{ctx['_fmt_num'](ctx['ia_saldo'])} m²**."
            )
    else:
        md(
            "👉 **Em resumo:**\n"
            f"- o uso residencial multifamiliar **{ctx['tipo_sigla']}** foi considerado **{ctx['status_curto'].lower()}** neste terreno;\n"
            f"- a zona permite ocupar até **{ctx['_fmt_pct'](ctx['to_max_pct'])}** do lote no térreo;\n"
            f"- pelo menos **{ctx['_fmt_pct'](ctx['tp_min_pct'])}** do terreno precisa continuar permeável;\n"
            f"- a construção pode chegar até **{ctx['_fmt_num'](ctx['ia_max'], 2) if ctx['ia_max'] not in (None, '') else '—'}** vezes a área do lote no total;\n"
            f"- e a altura deve respeitar o limite máximo permitido da zona."
        )
