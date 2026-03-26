from __future__ import annotations

from .common import md, formula_box


def render(ctx: dict) -> None:
    st = ctx["st"]
    if ctx['tp_min_pct'] is None or ctx['tp_m2'] is None:
        st.info("Ainda não foi possível calcular a Taxa de Permeabilidade com base na regra carregada.")
        return

    md(f"A zona exige **{ctx['_fmt_pct'](ctx['tp_min_pct'])}** de área permeável.")
    formula_box(ctx, f"{ctx['_fmt_num'](ctx['lot_area_f'])} × {ctx['_fmt_pct'](ctx['tp_min_pct'])} = {ctx['_fmt_num'](ctx['tp_m2'])} obrigatórios permeáveis")
    md("Isso quer dizer que parte do terreno precisa continuar permitindo a infiltração da água da chuva no solo.")
    if ctx['a_adotada'] is not None and ctx['area_livre_projeto'] is not None:
        md("**Área livre considerando a área adotada no relatório**")
        md(
            f"Como o relatório adotou **{ctx['_fmt_num'](ctx['a_adotada'])} m²** no térreo, a área livre remanescente no lote fica assim:\n\n"
            f"👉 **{ctx['_fmt_num'](ctx['lot_area_f'])} m² − {ctx['_fmt_num'](ctx['a_adotada'])} m² = {ctx['_fmt_num'](ctx['area_livre_projeto'])} m²**"
        )
        md(f"**Área livre remanescente no lote: {ctx['_fmt_num'](ctx['area_livre_projeto'])} m²**")
        md(f"Desses, **{ctx['_fmt_num'](ctx['tp_m2'])} m²** precisam permanecer permeáveis.")
        if ctx['area_impermavel_pos_tp'] is not None:
            md(
                f"Assim, restam:\n\n👉 **{ctx['_fmt_num'](ctx['area_livre_projeto'])} m² − {ctx['_fmt_num'](ctx['tp_m2'])} m² = {ctx['_fmt_num'](ctx['area_impermavel_pos_tp'])} m²**\n\n"
                f"**Área que ainda pode receber piso impermeável: {ctx['_fmt_num'](ctx['area_impermavel_pos_tp'])} m²**"
            )
        leitura_tp = (
            f"como a área pretendida inicial de **{ctx['_fmt_num'](ctx['built_ground'])} m²** excedeu o limite adotado no relatório, os cálculos passaram a considerar **{ctx['_fmt_num'](ctx['a_adotada'])} m²** no térreo"
            if (ctx['built_ground'] is not None and ctx['built_ground'] > ctx['a_adotada'])
            else f"os cálculos passaram a considerar a própria área pretendida informada, de **{ctx['_fmt_num'](ctx['a_adotada'])} m²** no térreo"
        )
        md(
            f"👉 **Leitura prática:** {leitura_tp}. Com isso, a área livre remanescente fica em **{ctx['_fmt_num'](ctx['area_livre_projeto'])} m²**, "
            f"dos quais **{ctx['_fmt_num'](ctx['tp_m2'])} m²** devem permanecer permeáveis para atender à exigência mínima da zona."
        )
