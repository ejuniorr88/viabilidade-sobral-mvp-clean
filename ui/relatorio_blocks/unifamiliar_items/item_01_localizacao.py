from __future__ import annotations
# contrato: Uso informado:
# contrato: Área do terreno:

from ui.report_components import render_html_fragment, render_section_card, render_summary_grid

from .common import fmt_num


def get_item_html(ctx: dict) -> str:
    body = (
        '<p class="vf-lead">Aqui estão os dados principais usados nesta análise.</p>'
        + render_summary_grid([
            ("Uso informado", str(ctx['uso_label'])),
            ("Área do terreno", f"{fmt_num(ctx['A'])} m²"),
            ("Dimensões", f"{fmt_num(ctx['W'])} m × {fmt_num(ctx['D'])} m"),
            ("Zona", str(ctx['zone'])),
            ("Subzona / setor", str(ctx['subzone_code'])),
            ("Tipo de lote", str(ctx['tipo_lote'])),
            ("Via", str(ctx['via'])),
            ("Tipo de via", str(ctx['via_tipo'])),
        ])
        + '<p class="vf-lead">Essas informações são a base de todo o relatório.</p>'
    )
    return render_section_card(1, 'Onde está localizado o terreno?', body)


def render(ctx: dict) -> None:
    render_html_fragment(get_item_html(ctx))
