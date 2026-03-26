from __future__ import annotations
from . import common

def render(ctx):
    if ctx["to_max_pct"] in (None, "") or ctx["to_m2"] is None:
        common.st.info("Ainda não foi possível calcular a ocupação máxima no térreo com base na regra carregada.")
        return
    common.st.markdown(f"A zona permite ocupar até **{common._fmt_pct(ctx['to_max_pct'])}** do terreno no térreo.")
    common._formula_box(f"{common._fmt_num(ctx['lot_area_f'])} × {common._fmt_pct(ctx['to_max_pct'])} = {common._fmt_num(ctx['to_m2'])}")
    common.st.markdown("Esse é o limite máximo permitido pela Taxa de Ocupação (TO).")
    if ctx["built_ground"] is not None and ctx["built_ground"] > 0:
        common.st.markdown(f"A área construída pretendida informada foi de **{common._fmt_num(ctx['built_ground'])} m²**.")
    if ctx["is_r21"]:
        common.st.markdown(
            f"No caso do **R2.1**, quando a zona admitir leitura semelhante ao unifamiliar, o teto urbanístico do térreo pode chegar a **{common._fmt_num(ctx['to_m2'])} m²** pela TO."
        )
    else:
        common.st.markdown(
            f"No caso do **{common._tipo_multifamiliar_label(ctx['multi_tipo'], ctx['use_type_code']).split(' — ')[0]}**, além da TO máxima, a implantação também precisa respeitar os **recuos obrigatórios da zona**."
        )
        common.st.markdown(
            f"### Recuos da zona\n- **Frontal:** {common._fmt_num(ctx['rec_fr'])}\n- **Laterais:** {common._fmt_num(ctx['rec_lat'])}\n- **Fundo:** {common._fmt_num(ctx['rec_fun'])}"
        )
    if ctx["W_util"] is not None and ctx["D_util"] is not None and ctx["A_recuos"] is not None:
        common.st.markdown(f"### Cálculo da largura útil\nA largura original do lote é de **{common._fmt_num(ctx['lot_front'])} m**.")
        common._formula_box(f"{common._fmt_num(ctx['lot_front'])} − recuos laterais = {common._fmt_num(ctx['W_util'])}")
        common.st.markdown(f"**Largura útil: {common._fmt_num(ctx['W_util'])}**")
        common.st.markdown(f"### Cálculo da profundidade útil\nA profundidade original do lote é de **{common._fmt_num(ctx['lot_depth'])} m**.")
        common._formula_box(f"{common._fmt_num(ctx['lot_depth'])} − recuo frontal − recuo de fundo = {common._fmt_num(ctx['D_util'])}")
        common.st.markdown(f"**Profundidade útil: {common._fmt_num(ctx['D_util'])}**")
        common.st.markdown("### Cálculo da área útil de implantação")
        common._formula_box(f"{common._fmt_num(ctx['W_util'])} × {common._fmt_num(ctx['D_util'])} = {common._fmt_num(ctx['A_recuos'])}")
    if ctx["a_adotada"] is not None and ctx["to_utilizada_pct"] is not None:
        common.st.markdown("**TO efetiva considerada no relatório**")
        common._formula_box(f"{common._fmt_num(ctx['a_adotada'])} ÷ {common._fmt_num(ctx['lot_area_f'])} = {common._fmt_pct(ctx['to_utilizada_pct'])}")
        common.st.markdown(f"**TO do projeto considerada no relatório: {common._fmt_pct(ctx['to_utilizada_pct'])}**")
        leitura_base = f"Como a área pedida foi de **{common._fmt_num(ctx['built_ground'])} m²**" if (ctx['built_ground'] is not None and ctx['built_ground'] > ctx['a_adotada']) else f"Como a área adotada no relatório foi de **{common._fmt_num(ctx['a_adotada'])} m²**"
        complemento = f"Ao aplicar todos os recuos da zona, o espaço que realmente sobra para implantar a edificação no térreo fica em **{common._fmt_num(ctx['A_recuos'])} m²**." if ctx['A_recuos'] is not None else ""
        common.st.markdown(f"👉 **Leitura prática:** pela TO, o lote poderia ocupar até **{common._fmt_num(ctx['to_m2'])} m²** no térreo. {leitura_base}, o relatório adotou **{common._fmt_num(ctx['a_adotada'])} m²** para os cálculos deste cenário. {complemento}")
