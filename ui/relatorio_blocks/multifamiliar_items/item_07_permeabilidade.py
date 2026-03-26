from __future__ import annotations
from . import common

def render(ctx):
    if ctx["tp_min_pct"] is None or ctx["tp_m2"] is None:
        common.st.info("Ainda não foi possível calcular a Taxa de Permeabilidade com base na regra carregada.")
        return
    common.st.markdown(f"A zona exige **{common._fmt_pct(ctx['tp_min_pct'])}** de área permeável.")
    common._formula_box(f"{common._fmt_num(ctx['lot_area_f'])} × {common._fmt_pct(ctx['tp_min_pct'])} = {common._fmt_num(ctx['tp_m2'])} obrigatórios permeáveis")
    common.st.markdown("Isso quer dizer que parte do terreno precisa continuar permitindo a infiltração da água da chuva no solo.")
    if ctx["a_adotada"] is not None and ctx["area_livre_projeto"] is not None:
        common.st.markdown("**Área livre considerando a área adotada no relatório**")
        common.st.markdown(
            f"Como o relatório adotou **{common._fmt_num(ctx['a_adotada'])} m²** no térreo, a área livre remanescente no lote fica assim:\n\n👉 **{common._fmt_num(ctx['lot_area_f'])} m² − {common._fmt_num(ctx['a_adotada'])} m² = {common._fmt_num(ctx['area_livre_projeto'])} m²**"
        )
        common.st.markdown(f"**Área livre remanescente no lote: {common._fmt_num(ctx['area_livre_projeto'])} m²**")
        common.st.markdown(f"Desses, **{common._fmt_num(ctx['tp_m2'])} m²** precisam permanecer permeáveis.")
        if ctx["area_impermavel_pos_tp"] is not None:
            common.st.markdown(
                f"Assim, restam:\n\n👉 **{common._fmt_num(ctx['area_livre_projeto'])} m² − {common._fmt_num(ctx['tp_m2'])} m² = {common._fmt_num(ctx['area_impermavel_pos_tp'])} m²**\n\n**Área que ainda pode receber piso impermeável: {common._fmt_num(ctx['area_impermavel_pos_tp'])} m²**"
            )
