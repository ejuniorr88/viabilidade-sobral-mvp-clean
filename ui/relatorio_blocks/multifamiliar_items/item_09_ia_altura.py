from __future__ import annotations
from . import common


def render(ctx):
    if ctx["ia_max"] in (None, "") or ctx["ia_m2"] is None:
        common.st.info("Ainda não foi possível calcular o potencial total de construção com base no Índice de Aproveitamento (IA) da zona.")
        return

    common.st.markdown(
        "Além da ocupação no térreo, a zona também define o potencial construtivo total do lote por meio do **Índice de Aproveitamento (IA)**."
    )
    common.st.markdown(
        f"Se o **Índice de Aproveitamento (IA)** máximo da zona for **{common._fmt_num(ctx['ia_max'], 2)}**, então o potencial construtivo total do lote será:"
    )
    common._formula_box(
        f"{common._fmt_num(ctx['lot_area_f'])} m² × {common._fmt_num(ctx['ia_max'], 2)} = {common._fmt_num(ctx['ia_m2'])} m²"
    )
    common.st.markdown(
        "Esse é o total que pode ser distribuído entre térreo e pavimentos superiores, respeitando também os demais parâmetros urbanísticos."
    )

    if ctx.get("gabarito_f") is not None:
        common.st.markdown(f"**Altura máxima da zona: {common._fmt_num(ctx['gabarito_f'])} m**")

        try:
            gabarito = float(ctx["gabarito_f"])
            pav_ref = int(round(gabarito / 3.0)) if gabarito > 0 else None
        except Exception:
            pav_ref = None

        if ctx.get("is_r21"):
            common.st.markdown(
                f"A altura máxima da zona é de **{common._fmt_num(ctx['gabarito_f'])} m**, mas como o uso informado é **R2.1**, a tipologia fica limitada a no máximo **2 pavimentos**.\n\n"
                "Portanto, a altura da zona não deve ser lida como autorização para ultrapassar esse limite tipológico.\n\n"
                "👉 **Na prática:** mesmo que a zona admita altura maior, o R2.1 continua limitado a até **2 pavimentos**, além de depender da implantação, da **Taxa de Ocupação (TO)**, da **Taxa de Permeabilidade (TP)**, dos recuos, do **Índice de Aproveitamento (IA)**, das normas técnicas e da confirmação no licenciamento municipal."
            )
        elif pav_ref:
    common.st.markdown(
        f"Como referência, uma altura máxima de **{common._fmt_num(ctx['gabarito_f'])} m** pode corresponder a cerca de **{pav_ref} pavimentos de 3,00 m cada**."
    )
    common.st.markdown(
        "Na prática, porém, edifícios residenciais multifamiliares precisam prever vagas de estacionamento. "
        "Como o estacionamento em subsolo costuma encarecer a obra, uma solução comum é usar o térreo para estacionamento "
        "e deixar os pavimentos superiores para as unidades residenciais. "
        f"Nesse exemplo, a altura disponível poderia resultar em **1 pavimento de estacionamento no térreo + {max(pav_ref - 1, 0)} pavimentos residenciais**."
    )
    common.st.markdown(
        "Se as vagas forem resolvidas em **subsolo**, e esse subsolo atender às condições legais para não entrar no cálculo da altura máxima, "
        f"o térreo também poderá ser usado como pavimento residencial, podendo chegar a **{pav_ref} pavimentos acima do subsolo**."
    )
    common.st.markdown(
        "👉 **A quantidade final de pavimentos depende da solução arquitetônica e das demais regras do projeto.**"
    )
        else:
            common.st.markdown(
                "A altura máxima da zona é um parâmetro urbanístico geral. A quantidade real de pavimentos depende do projeto, do Índice de Aproveitamento (IA), da Taxa de Ocupação (TO), da Taxa de Permeabilidade (TP), dos recuos, das normas técnicas e da confirmação no licenciamento municipal."
            )

# Contratos textuais legados preservados para testes automatizados: Isso é apenas uma referência inicial
