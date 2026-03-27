from __future__ import annotations
from . import common

def render(ctx):
    if ctx["ia_max"] in (None, "") or ctx["ia_m2"] is None:
        common.st.info("Ainda não foi possível calcular o potencial total de construção com base no IA da zona.")
        return

    common.st.markdown("Além do limite no térreo, existe o limite total permitido.")
    common.st.markdown(f"**Índice de Aproveitamento (IA): {common._fmt_num(ctx['ia_max'], 2)}**")
    common._formula_box(f"{common._fmt_num(ctx['lot_area_f'])} × {common._fmt_num(ctx['ia_max'], 2)} = {common._fmt_num(ctx['ia_m2'])} no total")
    common.st.markdown(f"Isso significa que você pode distribuir até **{common._fmt_num(ctx['ia_m2'])}** somando todos os pavimentos.")
    common.st.markdown(f"**Altura permitida máxima da zona: {common._fmt_num(ctx['gabarito_f'])}**")
    common.st.markdown(
        "Estimativa simples para ter noção do número de pavimentos: "
        "essa leitura serve apenas como referência inicial. O número real de andares depende do projeto, "
        "do pé-direito adotado, da estrutura, da circulação vertical e das demais exigências aplicáveis."
    )
