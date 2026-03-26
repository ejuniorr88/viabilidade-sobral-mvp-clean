from __future__ import annotations

from .common import md, formula_box


def render(ctx: dict) -> None:
    st = ctx["st"]
    if ctx['to_max_pct'] in (None, '') or ctx['to_m2'] is None:
        st.info("Ainda não foi possível calcular a ocupação máxima no térreo com base na regra carregada.")
        return

    md(f"A zona permite ocupar até **{ctx['_fmt_pct'](ctx['to_max_pct'])}** do terreno no térreo.")
    formula_box(ctx, f"{ctx['_fmt_num'](ctx['lot_area_f'])} × {ctx['_fmt_pct'](ctx['to_max_pct'])} = {ctx['_fmt_num'](ctx['to_m2'])}")
    md("Esse é o limite máximo permitido pela Taxa de Ocupação (TO).")
    if ctx['built_ground'] is not None and ctx['built_ground'] > 0:
        md(f"A área construída pretendida informada foi de **{ctx['_fmt_num'](ctx['built_ground'])} m²**.")

    if ctx['is_r21']:
        md(
            f"No caso do **R2.1**, quando a zona admitir leitura semelhante ao unifamiliar, o teto urbanístico do térreo pode chegar a **{ctx['_fmt_num'](ctx['to_m2'])} m²** pela TO."
        )
        if ctx['built_ground'] is not None and ctx['a_adotada'] is not None:
            if ctx['built_ground'] > ctx['a_adotada']:
                md(f"Como a área pretendida de **{ctx['_fmt_num'](ctx['built_ground'])} m²** excede esse limite, o relatório adotou **{ctx['_fmt_num'](ctx['a_adotada'])} m²** como base para os cálculos.")
            else:
                md(f"Como a área pretendida de **{ctx['_fmt_num'](ctx['built_ground'])} m²** está dentro do limite admissível, o relatório adotou esse mesmo valor como base para os cálculos.")
        if ctx['A_recuos'] is not None:
            md(f"Se você optar por aplicar integralmente os recuos da zona, a implantação prática no térreo cai para **{ctx['_fmt_num'](ctx['A_recuos'])} m²**.")
        md("👉 **Leitura específica do R2.1:** quando a zona permitir esse enquadramento, a implantação pode seguir lógica semelhante à do unifamiliar para parâmetros como TO, TP, IA e recuos.")
    else:
        md(f"No caso do **{ctx['tipo_sigla']}**, além da TO máxima, a implantação também precisa respeitar os **recuos obrigatórios da zona**.")
        if ctx['built_ground'] is not None and ctx['a_adotada'] is not None:
            if ctx['built_ground'] > ctx['a_adotada']:
                md(f"Como a área pretendida de **{ctx['_fmt_num'](ctx['built_ground'])} m²** excede o limite admissível neste cenário, o relatório adotou **{ctx['_fmt_num'](ctx['a_adotada'])} m²** como base para os cálculos.")
            else:
                md(f"Como a área pretendida de **{ctx['_fmt_num'](ctx['built_ground'])} m²** está dentro do limite admissível, o relatório adotou esse mesmo valor como base para os cálculos.")
        md(
            f"### Recuos da zona\n"
            f"- **Frontal:** {ctx['_fmt_num'](ctx['rec_fr'])}\n"
            f"- **Laterais:** {ctx['_fmt_num'](ctx['rec_lat'])}\n"
            f"- **Fundo:** {ctx['_fmt_num'](ctx['rec_fun'])}"
        )

    if ctx['W_util'] is not None and ctx['D_util'] is not None and ctx['A_recuos'] is not None:
        md(f"### Cálculo da largura útil\nA largura original do lote é de **{ctx['_fmt_num'](ctx['lot_front'])} m**.")
        formula_box(ctx, f"{ctx['_fmt_num'](ctx['lot_front'])} − recuos laterais = {ctx['_fmt_num'](ctx['W_util'])}")
        md(f"**Largura útil: {ctx['_fmt_num'](ctx['W_util'])}**")
        md(f"### Cálculo da profundidade útil\nA profundidade original do lote é de **{ctx['_fmt_num'](ctx['lot_depth'])} m**.")
        formula_box(ctx, f"{ctx['_fmt_num'](ctx['lot_depth'])} − recuo frontal − recuo de fundo = {ctx['_fmt_num'](ctx['D_util'])}")
        md(f"**Profundidade útil: {ctx['_fmt_num'](ctx['D_util'])}**")
        md("### Cálculo da área útil de implantação")
        formula_box(ctx, f"{ctx['_fmt_num'](ctx['W_util'])} × {ctx['_fmt_num'](ctx['D_util'])} = {ctx['_fmt_num'](ctx['A_recuos'])}")

    if ctx['a_adotada'] is not None and ctx['to_utilizada_pct'] is not None:
        md("**TO efetiva considerada no relatório**")
        formula_box(ctx, f"{ctx['_fmt_num'](ctx['a_adotada'])} ÷ {ctx['_fmt_num'](ctx['lot_area_f'])} = {ctx['_fmt_pct'](ctx['to_utilizada_pct'])}")
        md(f"**TO do projeto considerada no relatório: {ctx['_fmt_pct'](ctx['to_utilizada_pct'])}**")
        if ctx['built_ground'] is not None and ctx['built_ground'] > ctx['a_adotada']:
            leitura_base = f"Como a área pedida foi de **{ctx['_fmt_num'](ctx['built_ground'])} m²**"
        else:
            leitura_base = f"Como a área adotada no relatório foi de **{ctx['_fmt_num'](ctx['a_adotada'])} m²**"
        if ctx['is_r21']:
            complemento = f"Caso sejam aplicados integralmente os recuos da zona, a implantação prática cai para **{ctx['_fmt_num'](ctx['A_recuos'])} m²**." if ctx['A_recuos'] is not None else ""
            md(f"👉 **Leitura prática:** pela TO, o lote pode chegar até **{ctx['_fmt_num'](ctx['to_m2'])} m²** no térreo. {leitura_base}, o relatório adotou **{ctx['_fmt_num'](ctx['a_adotada'])} m²** como limite urbanístico para os cálculos. {complemento}")
        else:
            complemento = f"Ao aplicar todos os recuos da zona, o espaço que realmente sobra para implantar a edificação no térreo fica em **{ctx['_fmt_num'](ctx['A_recuos'])} m²**." if ctx['A_recuos'] is not None else ""
            md(f"👉 **Leitura prática:** pela TO, o lote poderia ocupar até **{ctx['_fmt_num'](ctx['to_m2'])} m²** no térreo. {leitura_base}, o relatório adotou **{ctx['_fmt_num'](ctx['a_adotada'])} m²** para os cálculos deste cenário. {complemento}")
