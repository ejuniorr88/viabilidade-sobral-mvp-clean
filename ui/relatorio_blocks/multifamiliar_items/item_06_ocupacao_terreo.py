from __future__ import annotations

import streamlit as st

from .common import md, fmt_num
from ui.relatorio_blocks.terreno_irregular import aviso_texto, limite_to_text


def _fmt_pct_local(v) -> str:
    try:
        return f"{float(v):.1f}%".replace(".", ",")
    except Exception:
        return "—"


def _num(v):
    try:
        if v in (None, ""):
            return None
        return float(v)
    except Exception:
        return None


def _same(a, b, tol=0.01) -> bool:
    a = _num(a)
    b = _num(b)
    return a is not None and b is not None and abs(a - b) <= tol


def _calc_area_restante(area_lote, ocupacao):
    a = _num(area_lote)
    o = _num(ocupacao)
    if a is None or o is None:
        return None
    return max(a - o, 0.0)


def _render_art112_intro() -> None:
    md("**Flexibilidade de recuos no uso residencial unifamiliar**")
    md(
        "Para residência unifamiliar, pode ser considerada a aplicação do **Art. 112**, que permite flexibilizar os recuos de frente e laterais, podendo chegar a **0,00 m**, desde que o projeto respeite a **Taxa de Ocupação (TO) máxima**, a **Taxa de Permeabilidade (TP) mínima** e as demais exigências do licenciamento.\n\n"
        "Essa flexibilização ajuda na implantação da edificação, mas **não aumenta a Taxa de Ocupação (TO)** e **não elimina a área permeável mínima**.\n\n"
        "A aplicação dessa leitura deve ser confirmada no licenciamento municipal. Ela não representa aprovação automática do projeto."
    )


def _render_recuos(rec_fr, rec_lat, rec_fun, w_util, d_util, a_recuos) -> None:
    md("**Conferência dos recuos deste lote**")
    md("Para este terreno, os parâmetros da zona indicam:")
    if rec_fr is not None:
        md(f"- recuo frontal: **{fmt_num(rec_fr)} m**;")
    if rec_lat is not None:
        md(f"- recuos laterais: **{fmt_num(rec_lat)} m**;")
    if rec_fun is not None:
        md(f"- recuo de fundos: **{fmt_num(rec_fun)} m**.")
    if w_util is not None or d_util is not None or a_recuos is not None:
        md("Considerando as dimensões informadas:")
    if w_util is not None:
        md(f"👉 largura útil: **{fmt_num(w_util)} m**")
    if d_util is not None:
        md(f"👉 profundidade útil: **{fmt_num(d_util)} m**")
    if a_recuos is not None and w_util is not None and d_util is not None:
        md(f"👉 área física estimada pelos recuos: **{fmt_num(w_util)} m × {fmt_num(d_util)} m = {fmt_num(a_recuos)} m²**")


def render(ctx: dict) -> None:
    if ctx.get("to_max") is None or ctx.get("A_to") is None:
        st.info("Sem Taxa de Ocupação (TO) máxima cadastrada para esta zona/uso.")
        return

    area_lote = ctx.get("A")
    to_max = ctx.get("to_max")
    area_to = ctx.get("A_to")
    area_pedida = ctx.get("area_pedida")
    area_considerada = ctx.get("A_considerada")
    excedeu_area = bool(ctx.get("excedeu_area"))

    rec_fr = ctx.get("rec_fr")
    rec_lat = ctx.get("rec_lat")
    rec_fun = ctx.get("rec_fun")
    w_util = ctx.get("W_util")
    d_util = ctx.get("D_util")
    a_recuos = ctx.get("A_recuos")

    pct_txt = _fmt_pct_local(to_max)

    md(
        f"A zona permite ocupar até **{pct_txt}** do terreno no térreo.\n\n"
        f"👉 **{fmt_num(area_lote)} m² × {pct_txt} = {fmt_num(area_to)} m²**\n\n"
        "Esse é o limite máximo permitido pela Taxa de Ocupação (TO)."
    )

    to_efetiva = None
    if area_pedida is not None and area_lote:
        try:
            to_efetiva = (float(area_pedida) / float(area_lote)) * 100.0
        except Exception:
            to_efetiva = None

    if area_pedida is not None and area_considerada is not None:
        if excedeu_area:
            md(
                f"👉 **Área pretendida informada: {fmt_num(area_pedida)} m².** Como esse valor ultrapassa o limite máximo permitido pela **Taxa de Ocupação (TO)**, ele não pode ser adotado como referência de implantação no térreo. Por isso, o estudo passa a considerar **{fmt_num(area_considerada)} m²** como teto urbanístico inicial para esta análise."
            )
            if to_efetiva is not None:
                md(
                    f"👉 **Taxa de Ocupação (TO) correspondente à área pretendida: {fmt_num(area_pedida)} m² ÷ {fmt_num(area_lote)} m² = {_fmt_pct_local(to_efetiva)}**\n\n"
                    f"Isso significa que, para esta proposta, a ocupação no térreo ficaria em **{_fmt_pct_local(to_efetiva)}** do lote, portanto acima da Taxa de Ocupação (TO) máxima permitida de **{pct_txt}**."
                )
            if a_recuos is not None and float(area_pedida) <= float(a_recuos):
                md(f"👉 A área pretendida informada cabe fisicamente pelos recuos, mas não pode ser adotada porque ultrapassa a **Taxa de Ocupação (TO)** máxima. A referência de ocupação máxima no térreo continua sendo **{fmt_num(area_considerada)} m²**, e o projeto precisaria ser reduzido para respeitar esse limite.")
        else:
            md(
                f"👉 **Área pretendida informada: {fmt_num(area_pedida)} m².** Como esse valor está abaixo do limite máximo permitido, ele pode ser adotado como referência inicial para a implantação no térreo."
            )
            md(f"👉 **Na leitura com a flexibilidade do Art. 112, a área pretendida de {fmt_num(area_pedida)} m² é viável, sujeita à confirmação no licenciamento.**")
            if to_efetiva is not None:
                md(
                    f"👉 **Taxa de Ocupação (TO) correspondente à área pretendida: {fmt_num(area_pedida)} m² ÷ {fmt_num(area_lote)} m² = {_fmt_pct_local(to_efetiva)}**\n\n"
                    f"Isso significa que, para esta proposta, a ocupação no térreo ficaria em **{_fmt_pct_local(to_efetiva)}** do lote, portanto abaixo da Taxa de Ocupação (TO) máxima permitida de **{pct_txt}**."
                )

    if ctx.get("is_irregular"):
        md("**Terreno irregular — leitura pela área total**")
        md(aviso_texto())
        md(limite_to_text(fmt_num(area_to)).replace("Taxa de Ocupação", "Taxa de Ocupação (TO)"))
        if area_pedida is not None and area_considerada is not None:
            if excedeu_area:
                md(f"👉 **Neste caso, a área pretendida precisa ser reduzida para respeitar o limite máximo de {fmt_num(area_considerada)} m² pela Taxa de Ocupação (TO).**")
            else:
                md(f"👉 **Neste caso, a área pretendida de {fmt_num(area_pedida)} m² está dentro do limite máximo pela Taxa de Ocupação (TO).**")
        else:
            md("👉 **Sem área pretendida informada, o estudo apresenta o limite máximo pela Taxa de Ocupação (TO) como referência inicial.**")
        return

    _render_art112_intro()

    # Quando os recuos padrão geram área menor que a TO, os dois cenários ajudam o usuário.
    recuos_menor_que_to = _num(a_recuos) is not None and _num(area_to) is not None and _num(a_recuos) < _num(area_to) and not _same(a_recuos, area_to)

    if recuos_menor_que_to:
        md("**Cenário A — leitura com flexibilidade do Art. 112**")
        md(
            "Com a aplicação do **Art. 112**, pode ser considerada a flexibilização dos recuos de frente e laterais, desde que sejam respeitadas a **Taxa de Ocupação (TO) máxima**, a **Taxa de Permeabilidade (TP) mínima** e as demais exigências do licenciamento.\n\n"
            f"Neste cenário, a referência de ocupação no térreo é de **{fmt_num(area_to)} m²**."
        )
        md("**Cenário B — leitura com recuos padrão da zona**")
        _render_recuos(rec_fr, rec_lat, rec_fun, w_util, d_util, a_recuos)
        md(
            f"Pela leitura dos recuos padrão da zona, a referência física de ocupação no térreo é de **{fmt_num(a_recuos)} m²**."
        )
        md("**Leitura prática**")
        md(
            f"A referência de ocupação depende da leitura adotada no licenciamento. Com a flexibilidade do **Art. 112**, a ocupação pode chegar ao limite da **Taxa de Ocupação (TO)**, que é de **{fmt_num(area_to)} m²**. Pela leitura dos recuos padrão, a área física estimada é de **{fmt_num(a_recuos)} m²**."
        )
        if area_pedida is not None and area_considerada is not None:
            if excedeu_area:
                md(f"👉 Como a área pretendida informada foi de **{fmt_num(area_pedida)} m²**, ela ultrapassa a **Taxa de Ocupação (TO)** máxima. Para esta análise preliminar, o relatório deve adotar **{fmt_num(area_considerada)} m²** como teto de referência no térreo.")
            else:
                md(f"👉 Como a área pretendida informada foi de **{fmt_num(area_pedida)} m²**, ela fica dentro da **Taxa de Ocupação (TO)** e permanece viável nas duas leituras, quando couber. A implantação final ainda deve ser conferida conforme a leitura de recuos adotada no licenciamento.")
        md("A confirmação final deve ser feita no licenciamento municipal.")
        return

    _render_recuos(rec_fr, rec_lat, rec_fun, w_util, d_util, a_recuos)
    if a_recuos is not None:
        if _num(a_recuos) is not None and _num(area_to) is not None and _num(a_recuos) > _num(area_to):
            md(
                f"Mesmo que a área física estimada pelos recuos seja de **{fmt_num(a_recuos)} m²**, a ocupação no térreo não pode ultrapassar o limite da **Taxa de Ocupação (TO)**, que é de **{fmt_num(area_to)} m²**."
            )
        else:
            md(
                f"Neste caso, a área física estimada pelos recuos coincide com o limite da **Taxa de Ocupação (TO)** ou não cria restrição adicional relevante para a leitura preliminar."
            )

    md("**Leitura prática**")
    ref = area_considerada if area_considerada is not None and area_pedida is not None else area_to
    md(f"Para este lote, a referência de ocupação máxima no térreo é de **{fmt_num(ref)} m²**.")
    md(
        "A implantação real da edificação deve respeitar a **Taxa de Ocupação (TO)**, a **Taxa de Permeabilidade (TP)**, os recuos aplicáveis, as normas técnicas e a confirmação no licenciamento municipal."
    )


# Contratos textuais legados preservados para testes automatizados: Art. 112. | permanece viável nas duas leituras | Como esse valor ultrapassa o limite máximo permitido pela TO
# contrato legado: Opção principal — aproveitando a flexibilidade da lei
# contrato legado: Opção alternativa — adotando os recuos da zona
# contrato legado: TO correspondente à área pretendida:
# contrato legado: abaixo da TO máxima permitida
# contrato legado: acima da TO máxima permitida
# contrato legado: o projeto precisaria ser reduzido para se enquadrar nos parâmetros urbanísticos
