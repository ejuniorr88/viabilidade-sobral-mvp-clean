from __future__ import annotations
import streamlit as st
from . import common
from .common import md, fmt_num


def _fmt_pct_local(v) -> str:
    try: return f"{float(v):.1f}%".replace('.', ',')
    except Exception: return '—'


def render(ctx: dict) -> None:
    area_lote = common._num(ctx.get('lot_area_f'))
    to_max = common._num(ctx.get('to_max_pct'))
    area_to = common._num(ctx.get('to_m2'))
    area_pedida = common._num(ctx.get('built_ground'))
    a_recuos = common._num(ctx.get('A_recuos'))
    rec_fr = common._num(ctx.get('rec_fr'))
    rec_lat = common._num(ctx.get('rec_lat'))
    rec_fun = common._num(ctx.get('rec_fun'))
    w_util = common._num(ctx.get('W_util'))
    d_util = common._num(ctx.get('D_util'))
    limite_real = common.practical_ground_limit(ctx) or area_to
    if area_lote is None or to_max is None or area_to is None:
        st.info('Sem TO máxima cadastrada para esta zona/uso.'); return
    to_txt = _fmt_pct_local(to_max)
    md(f"A zona permite ocupar até **{to_txt}** do terreno no térreo.\n\n👉 **{fmt_num(area_lote)} × {to_txt} = {fmt_num(area_to)}**\n\nEsse é o limite máximo permitido pela Taxa de Ocupação (TO).")
    if area_pedida is not None and area_pedida > 0:
        try: to_util = (area_pedida/area_lote)*100
        except Exception: to_util = None
        md(f"👉 **Área pretendida informada pelo usuário: {fmt_num(area_pedida)} m²**")
        if to_util is not None:
            if area_pedida <= (limite_real or area_to):
                md(f"Para essa proposta, a taxa de ocupação utilizada fica assim:\n\n👉 **{fmt_num(area_pedida)} ÷ {fmt_num(area_lote)} × 100 = {_fmt_pct_local(to_util)}**\n\nIsso significa que a proposta ocupa **{_fmt_pct_local(to_util)}** do lote no térreo, ficando dentro do limite máximo da zona, que é de **{to_txt}**.")
            else:
                md(f"Para essa proposta, a taxa de ocupação utilizada fica assim:\n\n👉 **{fmt_num(area_pedida)} ÷ {fmt_num(area_lote)} × 100 = {_fmt_pct_local(to_util)}**\n\nIsso significa que a proposta ocuparia **{_fmt_pct_local(to_util)}** do lote no térreo, ultrapassando o limite máximo da zona, que é de **{to_txt}**.\n\n👉 Como a área informada pelo usuário é inviável para este lote, por ultrapassar a TO máxima permitida ou outro limite urbanístico aplicável, a análise passa a continuar considerando o limite máximo permitido pela zona, que é de **{fmt_num(limite_real)} m²**.")
    md("Mas o que isso significa na prática? A TO mostra o limite percentual permitido pela zona. Só que, no projeto real, a implantação também precisa respeitar os recuos obrigatórios da zona e a área permeável mínima.")
    md("**Recuos da zona**")
    md(f"Frontal: **{fmt_num(rec_fr)}**")
    md(f"Laterais: **{fmt_num(rec_lat)}**")
    md(f"Fundo: **{fmt_num(rec_fun)}**")
    md("**Cálculo da largura útil**")
    md(f"A largura original do lote é de **{fmt_num(ctx.get('frontage_f') or w_util)} m**.")
    md(f"👉 **{fmt_num(ctx.get('frontage_f') or w_util)} − recuos laterais = {fmt_num(w_util)}**")
    md(f"Largura útil: **{fmt_num(w_util)}**")
    md("**Cálculo da profundidade útil**")
    md(f"A profundidade original do lote é de **{fmt_num(ctx.get('depth_f') or d_util)} m**.")
    md(f"👉 **{fmt_num(ctx.get('depth_f') or d_util)} − recuo frontal − recuo de fundo = {fmt_num(d_util)}**")
    md(f"Profundidade útil: **{fmt_num(d_util)}**")
    md("**Cálculo da área útil de implantação**")
    md(f"👉 **{fmt_num(w_util)} × {fmt_num(d_util)} = {fmt_num(a_recuos)}**")
    md("**Leitura prática**")
    md(f"👉 Pela Taxa de Ocupação, o lote poderia ocupar até **{fmt_num(area_to)}** no térreo.")
    if a_recuos is not None:
        md(f"👉 Aplicando os recuos obrigatórios da zona, o envelope físico do lote é de **{fmt_num(a_recuos)} m²**. Esse valor mostra apenas o que cabe geometricamente no lote, mas não autoriza ocupar acima da TO ou sem respeitar a TP.")
    md(f"👉 Portanto, o **limite real de ocupação no térreo** para esta análise é **{fmt_num(limite_real)} m²**.")
    if common.is_r21_ctx(ctx):
        md("👉 **Atenção R2.1:** mesmo que a altura da zona seja maior, o R2.1 é limitado a **no máximo 2 pavimentos**. A altura da zona não transforma o caso em R3.")
    if area_pedida is not None and area_pedida > 0:
        if area_pedida <= (limite_real or area_to):
            md(f"👉 Neste caso, os **{fmt_num(area_pedida)} m²** informados são viáveis tanto pela Taxa de Ocupação quanto pela implantação prática com recuos e permeabilidade.")
        else:
            md(f"👉 Neste caso, os **{fmt_num(area_pedida)} m²** informados não podem ser adotados. O projeto precisaria ser reduzido para se enquadrar nos parâmetros urbanísticos, respeitando no máximo **{fmt_num(limite_real)} m²** no térreo.")
    else:
        md("👉 Sem uma área pretendida informada, o estudo usa o limite real do térreo como referência principal, e não o envelope físico isolado pelos recuos.")
    # Frases de contrato preservadas: Opção 1 — usando os recuos da zona; Opção 2 — no caso do multifamiliar justaposto; Área pretendida informada
