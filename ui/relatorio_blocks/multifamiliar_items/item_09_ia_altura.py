from __future__ import annotations
from . import common

def render(ctx):
    if ctx["ia_max"] in (None, "") or ctx["ia_m2"] is None:
        common.st.info("Ainda não foi possível calcular o potencial total de construção com base no IA da zona.")
        return
    common.st.markdown("Além da ocupação no térreo, a zona também define o potencial construtivo total do lote por meio do **Índice de Aproveitamento (IA)**.")
    common.st.markdown(f"**Índice de Aproveitamento (IA): {common._fmt_num(ctx['ia_max'], 2)}**")
    common._formula_box(f"{common._fmt_num(ctx['lot_area_f'])} × {common._fmt_num(ctx['ia_max'], 2)} = {common._fmt_num(ctx['ia_m2'])} no total")
    common.st.markdown(f"Isso significa que você pode distribuir até **{common._fmt_num(ctx['ia_m2'])}** somando todos os pavimentos.")
    if ctx["a_adotada"] is not None and ctx["ia_saldo"] is not None:
        common.st.markdown(
            f"Como o relatório adotou **{common._fmt_num(ctx['a_adotada'])} m²** no térreo, o saldo estimado para crescer acima fica assim:\n\n👉 **{common._fmt_num(ctx['ia_m2'])} m² − {common._fmt_num(ctx['a_adotada'])} m² = {common._fmt_num(ctx['ia_saldo'])} m²**\n\n**Saldo estimado para pavimentos superiores: {common._fmt_num(ctx['ia_saldo'])} m²**"
        )
    common.st.markdown(f"**Altura permitida máxima da zona: {common._fmt_num(ctx['gabarito_f'])}**")
