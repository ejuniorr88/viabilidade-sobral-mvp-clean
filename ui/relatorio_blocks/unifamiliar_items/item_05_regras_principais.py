from __future__ import annotations
# contrato: TO máxima:

from ui.report_components import render_html_fragment, render_info_box, render_section_card, render_summary_grid

from .common import fmt_pct, fmt_num


def get_item_html(ctx: dict) -> str:
    body = ''.join([
        '<p class="vf-lead">Depois de entender a zona, o próximo passo é ver as regras básicas do lote.</p>',
        render_info_box(
            'Resumo das regras',
            render_summary_grid([
                ('TO máxima', fmt_pct(ctx['to_max'])),
                ('TP mínima', fmt_pct(ctx['tp_min'])),
                ('IA máximo', fmt_num(ctx['ia_max']) if ctx['ia_max'] is not None else '—'),
                ('IA mínimo', ctx['ia_min_texto']),
                ('Recuos', ctx['recuos_resumo']),
                ('Altura máxima', f"{fmt_num(ctx['gabarito_m'])} m"),
            ])
        ),
        '<p class="vf-lead">Essas são as regras que mais impactam o projeto.</p>',
    ])
    return render_section_card(5, 'Regras principais para este terreno', body)


def render(ctx: dict) -> None:
    render_html_fragment(get_item_html(ctx))
