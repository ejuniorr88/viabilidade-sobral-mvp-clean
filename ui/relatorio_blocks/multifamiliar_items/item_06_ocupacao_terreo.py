from __future__ import annotations

from . import common


def render(ctx):
    if ctx["to_max_pct"] in (None, "") or ctx["to_m2"] is None:
        common.st.info("Ainda não foi possível calcular a ocupação máxima no térreo com base na regra carregada.")
        return

    common.st.markdown(
        f"A zona permite ocupar até **{common._fmt_pct(ctx['to_max_pct'])}** do terreno no térreo."
    )
    common._formula_box(
        f"{common._fmt_num(ctx['lot_area_f'])} × {common._fmt_pct(ctx['to_max_pct'])} = {common._fmt_num(ctx['to_m2'])}"
    )
    common.st.markdown("Esse é o limite máximo permitido pela Taxa de Ocupação (TO).")
    common.st.markdown(
        f"Na prática, isso significa que a edificação não pode ultrapassar **{common._fmt_num(ctx['to_m2'])} m²** no chão, considerando a ocupação máxima permitida pela zona."
    )

    common.st.markdown("**Opção 1 — usando os recuos da zona**")
    common.st.markdown("No caso de usar todos os recuos conforme a zona, a área útil de implantação fica assim:")

    if ctx["W_util"] is not None:
        common.st.markdown("**1. Cálculo da largura útil**")
        common.st.markdown(f"A largura original do lote é de **{common._fmt_num(ctx['lot_front'])} m**.")
        common.st.markdown("Como a zona exige:")
        common.st.markdown(f"- **{common._fmt_num(ctx['rec_lat'])} m** de recuo lateral de um lado")
        common.st.markdown(f"- **{common._fmt_num(ctx['rec_lat'])} m** de recuo lateral do outro lado")
        common.st.markdown("fazemos:")
        common._formula_box(
            f"{common._fmt_num(ctx['lot_front'])} − {common._fmt_num(ctx['rec_lat'])} − {common._fmt_num(ctx['rec_lat'])} = {common._fmt_num(ctx['W_util'])}"
        )
        common.st.markdown(f"**Largura útil: {common._fmt_num(ctx['W_util'])} m**")

    if ctx["D_util"] is not None:
        common.st.markdown("**2. Cálculo da profundidade útil**")
        common.st.markdown(f"A profundidade original do lote é de **{common._fmt_num(ctx['lot_depth'])} m**.")
        common.st.markdown("Como a zona exige:")
        common.st.markdown(f"- **{common._fmt_num(ctx['rec_fr'])} m** de recuo frontal")
        common.st.markdown(f"- **{common._fmt_num(ctx['rec_fun'])} m** de recuo de fundo")
        common.st.markdown("fazemos:")
        common._formula_box(
            f"{common._fmt_num(ctx['lot_depth'])} − {common._fmt_num(ctx['rec_fr'])} − {common._fmt_num(ctx['rec_fun'])} = {common._fmt_num(ctx['D_util'])}"
        )
        common.st.markdown(f"**Profundidade útil: {common._fmt_num(ctx['D_util'])} m**")

    if ctx["A_recuos"] is not None:
        common.st.markdown("**3. Cálculo da área útil de implantação**")
        common._formula_box(
            f"{common._fmt_num(ctx['W_util'])} × {common._fmt_num(ctx['D_util'])} = {common._fmt_num(ctx['A_recuos'])}"
        )
        common.st.markdown(
            f"**Leitura prática:** isso significa que, mesmo que a zona permita ocupar até **{common._fmt_num(ctx['to_m2'])} m²** pela TO, ao aplicar todos os recuos da zona o espaço que realmente sobra para implantar a edificação no térreo fica em **{common._fmt_num(ctx['A_recuos'])} m²**."
        )

    common.st.markdown("**Opção 2 — no caso do R2.1**")
    common.st.markdown(
        f"Quando a zona admitir leitura semelhante ao unifamiliar, o projeto pode adotar essa lógica de implantação."
    )
    common._formula_box(
        f"Nesse caso, o aproveitamento do térreo pode chegar ao limite máximo de {common._fmt_num(ctx['to_m2'])} m² pela Taxa de Ocupação (TO)"
    )
    common.st.markdown(
        "desde que também sejam respeitadas as demais exigências urbanísticas aplicáveis ao caso."
    )

    common.st.markdown("**Leitura final**")
    leitura_recuos = (
        f"Quando são aplicados integralmente os recuos da zona, a área útil de implantação fica em **{common._fmt_num(ctx['A_recuos'])} m²**. "
        if ctx["A_recuos"] is not None
        else ""
    )
    common.st.markdown(
        f"A Taxa de Ocupação (TO) permite ocupar até **{common._fmt_num(ctx['to_m2'])} m²** no térreo. {leitura_recuos}Já no caso do **R2.1**, quando a zona admitir leitura semelhante ao unifamiliar, o aproveitamento do térreo pode chegar ao limite máximo de **{common._fmt_num(ctx['to_m2'])} m²** pela TO, desde que também sejam respeitadas as demais exigências urbanísticas aplicáveis ao caso, como adequabilidade, permeabilidade e demais parâmetros da zona."
    )
