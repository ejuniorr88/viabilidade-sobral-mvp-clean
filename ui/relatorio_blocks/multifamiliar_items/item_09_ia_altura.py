from __future__ import annotations
from . import common


def render(ctx):
    if ctx['ia_max'] in (None, '') or ctx['ia_m2'] is None:
        common.st.info('Ainda não foi possível calcular o potencial total de construção com base no IA da zona.')
        return
    common.st.markdown('Além da ocupação no térreo, a zona também define o potencial construtivo total do lote por meio do Índice de Aproveitamento (IA).')
    common.st.markdown(f"Se o IA máximo da zona for **{common._fmt_num(ctx['ia_max'], 2)}**, então o potencial construtivo total do lote será:")
    common._formula_box(f"{common._fmt_num(ctx['lot_area_f'])} m² × {common._fmt_num(ctx['ia_max'], 2)} = {common._fmt_num(ctx['ia_m2'])} m²")
    common.st.markdown('Esse é o total que pode ser distribuído entre térreo e pavimentos superiores, respeitando também os demais parâmetros urbanísticos.')
    if ctx.get('gabarito_f') is not None:
        common.st.markdown(f"**Altura máxima da zona: {common._fmt_num(ctx['gabarito_f'])} m**")
        if common.is_r21_ctx(ctx):
            common.st.warning('**Atenção R2.1:** embora a altura da zona seja exibida, a tipologia R2.1 é limitada a **no máximo 2 pavimentos**. Portanto, não se deve estimar 4 ou 5 pavimentos para esse enquadramento.')
        else:
            try:
                gabarito = float(ctx['gabarito_f']); pav_ref = int(round(gabarito / 3.0)) if gabarito > 0 else None
            except Exception:
                pav_ref = None
            if pav_ref:
                common.st.markdown(f"Exemplo simples para ter uma noção de andares: adotando um pé-direito médio de **3,00 m** por pavimento, a altura máxima de **{common._fmt_num(ctx['gabarito_f'])} m** pode permitir, em média, algo próximo de **{pav_ref} pavimentos**.")
            else:
                common.st.markdown('Exemplo simples para ter uma noção de andares: adotando um pé-direito médio de **3,00 m** por pavimento, a altura máxima da zona pode permitir uma estimativa inicial do número de pavimentos.')
        common.st.markdown('👉 **Isso é apenas uma referência inicial. Na prática, a quantidade real de andares depende também da laje, cobertura, platibanda, caixa d’água, da tipologia escolhida e da forma como o projeto será desenvolvido.**')
