from __future__ import annotations

from ui.report_components import render_html_fragment, render_info_box, render_section_card, render_summary_grid

from .common import fmt_num, fmt_pct

# contrato: "Se você quiser ver só o essencial deste terreno"
# contrato: "👉 **Em resumo:**"
# contrato: "você pode ocupar até **"

def get_item_html(ctx: dict) -> str:
    cards = [
        ('Uso analisado', ctx['uso_label']),
        ('Zona', ctx['zone_title']),
        ('Tipo de lote', ctx['tipo_lote']),
        ('Via', ctx['via']),
        ('Tipo de via', ctx['via_tipo']),
        ('TO máxima', fmt_pct(ctx['to_max'])),
        ('TP mínima', fmt_pct(ctx['tp_min'])),
        ('IA máximo', fmt_num(ctx['ia_max']) if ctx['ia_max'] is not None else '—'),
        ('Altura máxima', f"{fmt_num(ctx['gabarito_m'])} m"),
        ('Área máxima no térreo pela TO', f"{fmt_num(ctx['A_to'])} m²"),
        ('Área permeável mínima', f"{fmt_num(ctx['A_perm_min'])} m²"),
        ('Área total máxima estimada', f"{fmt_num(ctx['A_total'])} m²"),
    ]
    if ctx['area_pedida'] is not None and ctx['A_considerada'] is not None:
        cards.append(('Área pretendida informada', f"{fmt_num(ctx['area_pedida'])} m²"))
        cards.append(('Área adotada no relatório', f"{fmt_num(ctx['A_considerada'])} m²"))
        if ctx['to_projeto_pct'] is not None:
            cards.append(('TO efetiva considerada', fmt_pct(ctx['to_projeto_pct'])))
        if ctx['A_livre'] is not None:
            cards.append(('Área livre remanescente', f"{fmt_num(ctx['A_livre'])} m²"))
        if ctx['A_ia_saldo'] is not None:
            cards.append(('Saldo estimado pelo IA', f"{fmt_num(ctx['A_ia_saldo'])} m²"))

    body = ['<p class="vf-lead"><strong>Se você quiser ver só o essencial deste terreno, este é o resumo principal:</strong></p>', render_summary_grid(cards)]

    if ctx['area_pedida'] is not None and ctx['A_considerada'] is not None:
        if ctx['excedeu_area']:
            resumo = f'👉 <strong>Em resumo:</strong> você informou <strong>{fmt_num(ctx["area_pedida"])} m²</strong> no térreo, mas o relatório adotou <strong>{fmt_num(ctx["A_considerada"])} m²</strong> para respeitar os limites urbanísticos do lote. Com isso, a TO considerada ficou em <strong>{fmt_pct(ctx["to_projeto_pct"])}</strong>, a área livre remanescente em <strong>{fmt_num(ctx["A_livre"])} m²</strong> e o saldo estimado pelo IA em <strong>{fmt_num(ctx["A_ia_saldo"])} m²</strong>.'
            body.append(render_info_box('Resumo final', resumo, 'warning'))
        else:
            resumo = f'👉 <strong>Em resumo:</strong> o relatório considerou a área pretendida de <strong>{fmt_num(ctx["A_considerada"])} m²</strong> no térreo. Com isso, a TO considerada ficou em <strong>{fmt_pct(ctx["to_projeto_pct"])}</strong>, a área livre remanescente em <strong>{fmt_num(ctx["A_livre"])} m²</strong> e o saldo estimado pelo IA em <strong>{fmt_num(ctx["A_ia_saldo"])} m²</strong>.'
            body.append(render_info_box('Resumo final', resumo, 'success'))
    else:
        resumo = f'👉 <strong>Em resumo:</strong> você pode ocupar até <strong>{fmt_pct(ctx["to_max"])} </strong> do lote no térreo; precisa manter pelo menos <strong>{fmt_pct(ctx["tp_min"])} </strong> do terreno permeável; a construção pode chegar até <strong>{fmt_num(ctx["ia_max"]) if ctx["ia_max"] is not None else "—"}</strong> vezes a área do lote no total; e a altura deve respeitar o limite da zona.'
        body.append(render_info_box('Resumo final', resumo))

    return render_section_card(14, 'Resumo rápido final', ''.join(body))


def render(ctx: dict) -> None:
    render_html_fragment(get_item_html(ctx))
