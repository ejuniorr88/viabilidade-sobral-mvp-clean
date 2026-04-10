from __future__ import annotations

from ui.report_components import render_formula_box, render_html_fragment, render_info_box, render_section_card

from .common import fmt_num


def _fmt_pct_local(v) -> str:
    try:
        return f"{float(v):.1f}%".replace('.', ',')
    except Exception:
        return '—'


def get_item_html(ctx: dict) -> str:
    if ctx.get('to_max') is None or ctx.get('A_to') is None:
        return render_section_card(6, 'Quanto posso ocupar no térreo?', render_info_box('Sem dado', 'Sem TO máxima cadastrada para esta zona/uso.', 'warning'))

    area_lote = ctx.get('A')
    to_max = ctx.get('to_max')
    area_to = ctx.get('A_to')
    area_pedida = ctx.get('area_pedida')
    area_considerada = ctx.get('A_considerada')
    excedeu_area = bool(ctx.get('excedeu_area'))
    rec_fr = ctx.get('rec_fr')
    rec_lat = ctx.get('rec_lat')
    rec_fun = ctx.get('rec_fun')
    w_util = ctx.get('W_util')
    d_util = ctx.get('D_util')
    a_recuos = ctx.get('A_recuos')
    pct_txt = _fmt_pct_local(to_max)

    body = [
        f'<p class="vf-lead">A zona permite ocupar até <strong>{pct_txt}</strong> do terreno no térreo.</p>',
        render_formula_box(f'{fmt_num(area_lote)} m² × {pct_txt} = {fmt_num(area_to)} m²'),
        '<p class="vf-lead">Esse é o limite máximo permitido pela Taxa de Ocupação (TO).</p>',
    ]

    to_efetiva = None
    if area_pedida is not None and area_lote:
        try:
            to_efetiva = (float(area_pedida) / float(area_lote)) * 100.0
        except Exception:
            to_efetiva = None

    if area_pedida is not None and area_considerada is not None:
        if excedeu_area:
            body.append(render_info_box('Área pretendida informada', f'Como esse valor ultrapassa o limite máximo permitido pela TO, ele não pode ser adotado como referência de implantação no térreo. Por isso, o estudo passa a considerar <strong>{fmt_num(area_considerada)} m²</strong> como teto urbanístico inicial para esta análise.', 'warning'))
            if to_efetiva is not None:
                body.append(render_formula_box(f'TO correspondente à área pretendida: {fmt_num(area_pedida)} m² ÷ {fmt_num(area_lote)} m² = {_fmt_pct_local(to_efetiva)}'))
                body.append(f'<p class="vf-lead">Isso significa que, para esta proposta, a ocupação no térreo ficaria em <strong>{_fmt_pct_local(to_efetiva)}</strong> do lote, portanto acima da TO máxima permitida de <strong>{pct_txt}</strong>.</p>')
        else:
            body.append(render_info_box('Área pretendida informada', f'Como esse valor está abaixo do limite máximo permitido, ele pode ser adotado como referência inicial para a implantação no térreo.', 'success'))
            if to_efetiva is not None:
                body.append(render_formula_box(f'TO correspondente à área pretendida: {fmt_num(area_pedida)} m² ÷ {fmt_num(area_lote)} m² = {_fmt_pct_local(to_efetiva)}'))
                body.append(f'<p class="vf-lead">Isso significa que, para esta proposta, a ocupação no térreo ficaria em <strong>{_fmt_pct_local(to_efetiva)}</strong> do lote, portanto abaixo da TO máxima permitida de <strong>{pct_txt}</strong>.</p>')

    body += [
        '<p class="vf-lead">Como complemento a essa verificação, também é importante analisar a área que efetivamente cabe no lote, considerando os recuos aplicáveis.</p>',
        render_info_box('Art. 112.', 'Será aplicado, para as atividades atrativas de vizinhança de pequeno porte e para o uso residencial unifamiliar, a flexibilidade quanto aos recuos de frente e laterais, podendo zerar, desde que observado o cumprimento da Taxa de Permeabilidade Mínima e da Taxa de Ocupação Máxima da zona em que se encontra.'),
        render_info_box('Opção principal — aproveitando a flexibilidade da lei', f'Para este caso, a legislação admite zerar o recuo frontal e os recuos laterais. Assim, o térreo pode aproveitar melhor a área do lote, desde que continue respeitando a TO e a TP.<br><br><strong>Térreo máximo nesta opção: {fmt_num(area_to)} m²</strong>', 'success'),
    ]

    if area_pedida is not None and area_considerada is not None:
        if excedeu_area:
            body.append(render_info_box('Leitura da área pretendida', f'Como a área pretendida informada foi de <strong>{fmt_num(area_pedida)} m²</strong>, ela não é permitida nesta leitura, porque ultrapassa a Taxa de Ocupação máxima da zona. Portanto, para esta hipótese, o estudo passa a considerar <strong>{fmt_num(area_considerada)} m²</strong> como limite máximo admissível no térreo.', 'warning'))
        else:
            body.append(render_info_box('Leitura da área pretendida', f'Como a área pretendida informada foi de <strong>{fmt_num(area_pedida)} m²</strong>, ela cabe dentro desse limite máximo.', 'success'))

    recuos_txt = []
    if rec_fr is not None:
        recuos_txt.append(f'Frontal: <strong>{fmt_num(rec_fr)} m</strong>')
    if rec_lat is not None:
        recuos_txt.append(f'Laterais: <strong>{fmt_num(rec_lat)} m cada</strong>')
    if rec_fun is not None:
        recuos_txt.append(f'Fundo: <strong>{fmt_num(rec_fun)} m</strong>')
    alt_content = '<br>'.join(recuos_txt)
    if w_util is not None:
        alt_content += f'<br>Largura útil: <strong>{fmt_num(w_util)} m</strong>'
    if d_util is not None:
        alt_content += f'<br>Profundidade útil: <strong>{fmt_num(d_util)} m</strong>'
    if a_recuos is not None and w_util is not None and d_util is not None:
        alt_content += f'<br><br><strong>{fmt_num(w_util)} × {fmt_num(d_util)} = {fmt_num(a_recuos)} m²</strong>'
        alt_content += f'<br>👉 Nesse cenário, mesmo que a zona permita até <strong>{fmt_num(area_to)} m²</strong> pela TO, o limite físico de implantação, considerando os recuos, fica em <strong>{fmt_num(a_recuos)} m²</strong>.'
    body.append(render_info_box('Opção alternativa — adotando os recuos da zona', alt_content))

    if area_pedida is not None and area_considerada is not None:
        if excedeu_area:
            end_txt = 'o projeto precisaria ser reduzido para se enquadrar nos parâmetros urbanísticos'
            if a_recuos is not None:
                end_txt += f', respeitando no máximo {fmt_num(area_considerada)} m² pela TO, ou {fmt_num(a_recuos)} m² caso sejam adotados os recuos padrão da zona.'
            else:
                end_txt += f', respeitando no máximo {fmt_num(area_considerada)} m² pela TO.'
            body.append(render_info_box('Leitura prática', end_txt, 'warning'))
        else:
            if a_recuos is not None:
                body.append(render_info_box('Leitura prática', f'Na leitura com a flexibilidade do art. 112, a área pretendida de <strong>{fmt_num(area_pedida)} m²</strong> é viável. Na leitura com os recuos padrão da zona, a área útil de implantação cai para <strong>{fmt_num(a_recuos)} m²</strong>, mas a área pretendida de <strong>{fmt_num(area_pedida)} m²</strong> continua sendo viável. 👉 <strong>permanece viável nas duas leituras</strong>.', 'success'))
            else:
                body.append(render_info_box('Leitura prática', f'Na leitura com a flexibilidade do art. 112, a área pretendida de <strong>{fmt_num(area_pedida)} m²</strong> é viável.', 'success'))

    return render_section_card(6, 'Quanto posso ocupar no térreo?', ''.join(body))


def render(ctx: dict) -> None:
    render_html_fragment(get_item_html(ctx))
