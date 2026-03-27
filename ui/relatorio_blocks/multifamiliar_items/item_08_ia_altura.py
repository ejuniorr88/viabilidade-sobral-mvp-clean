from __future__ import annotations
from . import common

def render(ctx):
    if ctx["ia_max"] in (None, "") or ctx["ia_m2"] is None:
        common.st.info("Ainda não foi possível calcular o potencial total de construção com base no IA da zona.")
        return

    common.st.markdown("Além da ocupação no térreo, a zona também define o potencial construtivo total do lote por meio do Índice de Aproveitamento (IA).")
    common.st.markdown(
        f"Se o IA máximo da zona for **{common._fmt_num(ctx['ia_max'], 2)}**, então o potencial construtivo total do lote será:"
    )
    common.st.markdown(
        f"👉 **{common._fmt_num(ctx['lot_area_f'])} m² × {common._fmt_num(ctx['ia_max'], 2)} = {common._fmt_num(ctx['ia_m2'])} m²**"
    )
    common.st.markdown(
        f"Esse é o total que pode ser distribuído entre térreo e pavimentos superiores, respeitando também os demais parâmetros urbanísticos."
    )
    common.st.markdown(f"**Altura máxima da zona: {common._fmt_num(ctx['gabarito_f'])} m**")
    common.st.markdown(
        f"Exemplo simples para ter uma noção de andares: adotando um pé-direito médio de **3,00 m** por pavimento, a altura máxima de **{common._fmt_num(ctx['gabarito_f'])} m** pode permitir, em média, algo próximo de **{int(round((ctx['gabarito_f'] or 0) / 3)) if ctx['gabarito_f'] else 0} pavimentos**."
    )
    common.st.markdown(
        "👉 Isso é apenas uma referência inicial. Na prática, a quantidade real de andares depende também da laje, cobertura, platibanda, caixa d’água e da forma como o projeto será desenvolvido."
    )
