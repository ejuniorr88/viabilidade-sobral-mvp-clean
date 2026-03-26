from __future__ import annotations

from .common import md, formula_box


def render(ctx: dict) -> None:
    st = ctx["st"]
    if ctx['ia_max'] in (None, '') or ctx['ia_m2'] is None:
        st.info("Ainda não foi possível calcular o potencial total de construção com base no IA da zona.")
        return

    md("Além da ocupação no térreo, a zona também define o potencial construtivo total do lote por meio do **Índice de Aproveitamento (IA)**.")
    md(f"**Índice de Aproveitamento (IA): {ctx['_fmt_num'](ctx['ia_max'], 2)}**")
    formula_box(ctx, f"{ctx['_fmt_num'](ctx['lot_area_f'])} × {ctx['_fmt_num'](ctx['ia_max'], 2)} = {ctx['_fmt_num'](ctx['ia_m2'])} no total")
    md(f"Isso significa que você pode distribuir até **{ctx['_fmt_num'](ctx['ia_m2'])}** somando todos os pavimentos.")
    if ctx['a_adotada'] is not None and ctx['ia_saldo'] is not None:
        md(
            f"Como o relatório adotou **{ctx['_fmt_num'](ctx['a_adotada'])} m²** no térreo, o saldo estimado para crescer acima fica assim:\n\n"
            f"👉 **{ctx['_fmt_num'](ctx['ia_m2'])} m² − {ctx['_fmt_num'](ctx['a_adotada'])} m² = {ctx['_fmt_num'](ctx['ia_saldo'])} m²**\n\n"
            f"**Saldo estimado para pavimentos superiores: {ctx['_fmt_num'](ctx['ia_saldo'])} m²**"
        )
        md(
            f"👉 **Leitura prática:** considerando a área adotada de **{ctx['_fmt_num'](ctx['a_adotada'])} m²** no térreo, ainda restam **{ctx['_fmt_num'](ctx['ia_saldo'])} m²** de potencial construtivo pelo IA para crescimento em pavimentos superiores, desde que o projeto respeite também altura máxima, recuos, ventilação, iluminação, circulação e demais exigências aplicáveis."
        )
    md(f"**Altura permitida máxima da zona: {ctx['_fmt_num'](ctx['gabarito_f'])}**")
    if ctx['pav_est']:
        md(
            "**Estimativa simples para ter noção do número de pavimentos:**  \
"
            "essa leitura serve apenas como referência inicial. O número real de andares depende do projeto, do pé-direito adotado, "
            "da estrutura, da circulação vertical e das demais exigências aplicáveis."
        )
