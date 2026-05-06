from __future__ import annotations
import streamlit as st
from . import common
from .common import md, fmt_num


def _fmt_pct_local(v) -> str:
    try: return f"{float(v):.1f}%".replace('.', ',')
    except Exception: return '—'


def _show_area(lote, uso, perm):
    restante = lote - uso
    impermeavel = max(restante - perm, 0.0)
    md(f"Se você utilizar **{fmt_num(uso)}** no térreo:")
    md(f"👉 **Área restante no lote: {fmt_num(lote)} − {fmt_num(uso)} = {fmt_num(restante)}**")
    md("Desses:")
    md(f"- **{fmt_num(perm)}** devem permitir infiltração no solo")
    md(f"- **{fmt_num(impermeavel)}** podem receber piso impermeável")


def render(ctx: dict) -> None:
    area_lote = common._num(ctx.get('lot_area_f'))
    tp_min = common._num(ctx.get('tp_min_pct'))
    area_to = common._num(ctx.get('to_m2'))
    area_recuos = common._num(ctx.get('A_recuos'))
    area_pedida = common._num(ctx.get('built_ground'))
    if area_lote is None or tp_min is None:
        st.info('Sem Taxa de Permeabilidade cadastrada para esta zona/uso.'); return
    area_perm = area_lote * (tp_min/100.0)
    tp_txt = _fmt_pct_local(tp_min)
    limite_real = common.practical_ground_limit(ctx) or area_to
    md(f"A zona exige **{tp_txt}** de área permeável.\n\n👉 **{fmt_num(area_lote)} × {tp_txt} = {fmt_num(area_perm)} obrigatórios permeáveis**\n\nIsso quer dizer que parte do terreno precisa continuar permitindo a infiltração da água da chuva no solo.")
    if area_pedida is not None and area_pedida > 0 and limite_real is not None and area_pedida <= limite_real:
        md("**Cálculo usando a área digitada pelo usuário**")
        md(f"Como o usuário informou **{fmt_num(area_pedida)} m²** no térreo, a análise da permeabilidade passa a considerar esse valor.")
        _show_area(area_lote, area_pedida, area_perm)
        md(f"👉 **Leitura prática:** com a implantação proposta de **{fmt_num(area_pedida)} m²**, ainda sobram **{fmt_num(area_lote-area_pedida)} m²** livres no lote. Desse total, **{fmt_num(area_perm)} m²** precisam permanecer permeáveis.")
        return
    if area_pedida is not None and area_pedida > 0 and limite_real is not None and area_pedida > limite_real:
        md(f"👉 **Como a área digitada pelo usuário ({fmt_num(area_pedida)} m²) ultrapassa a TO máxima permitida ou outro limite real permitido, este item passa a analisar a permeabilidade com o limite ajustado de {fmt_num(limite_real)} m².**")
    md("**Cenário 1 — usando o máximo da TO**")
    uso_to = min(v for v in [area_to, limite_real] if v is not None)
    _show_area(area_lote, uso_to, area_perm)
    md("**Cenário 2 — usando a implantação pelos recuos da zona**")
    if area_recuos is not None:
        md(f"O envelope físico pelos recuos é de **{fmt_num(area_recuos)} m²**, mas ele não é uma ocupação possível quando ultrapassa a TO ou não deixa área livre suficiente para a TP.")
        if limite_real is not None:
            md(f"Para manter a TO e a TP, o limite real do térreo permanece em **{fmt_num(limite_real)} m²**.")
            _show_area(area_lote, limite_real, area_perm)
    md("👉 **Leitura prática:** no multifamiliar, quando a implantação aumenta, a área livre diminui. Por isso, quanto maior a ocupação do térreo, menor fica a sobra disponível além do mínimo exigido para a permeabilidade. O envelope físico pelos recuos não deve ser lido isoladamente como autorização para ocupar acima da TO ou descumprir a TP.")
