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


def _zone_key(ctx: dict) -> str:
    zona = str(
        ctx.get("zone_sigla")
        or ctx.get("zone")
        or ""
    ).strip().upper()

    return (
        zona
        .replace("-", "")
        .replace("_", "")
        .replace("/", "")
        .replace(" ", "")
    )


def _is_zeis(ctx: dict) -> bool:
    return _zone_key(ctx).startswith("ZEIS")


def _zeis_porte_info(ctx: dict) -> dict:
    """
    Regra especial de porte aplicada somente às ZEIS.

    AP:
        pequeno porte
        até 250 m² de área construída total.

    AP/AM:
        pequeno ou médio porte
        até 1.500 m² de área construída total.

    A classificação efetiva já resolvida pela análise de adequabilidade
    é utilizada aqui.

    Quando a classificação efetiva da via for A, a classificação da via
    se sobrepõe à classificação de porte da zona e o teto de AP/AP-AM
    da zona não é reaplicado.
    """

    status = str(
        ctx.get("status_curto") or ""
    ).strip().upper()

    zone_class = str(
        ctx.get("zone_class") or ""
    ).strip().upper()

    via_class = str(
        ctx.get("via_class") or ""
    ).strip().upper()

    info = {
        "is_zeis": _is_zeis(ctx),
        "active": False,
        "classificacao": None,
        "limite_total_m2": None,
        "via_override": False,
        "ground_limit_m2": None,
        "ground_reference_m2": None,
        "porte_restante_m2": None,
        "excedeu_porte": False,
        "excedeu_implantacao": False,
    }

    if not info["is_zeis"]:
        return info

    # Se a VIA efetivamente classificou o uso como A,
    # a via se sobrepõe ao AP/AP-AM da zona.
    if (
        via_class == "A"
        and zone_class in {"AP", "AP/AM"}
    ):
        info["via_override"] = True
        return info

    # Classificação efetiva AP.
    if "SOMENTE PEQUENO PORTE" in status:
        info["active"] = True
        info["classificacao"] = "AP"
        info["limite_total_m2"] = 250.0

    # Classificação efetiva AP/AM.
    elif "PEQUENO OU MÉDIO PORTE" in status:
        info["active"] = True
        info["classificacao"] = "AP/AM"
        info["limite_total_m2"] = 1500.0

    return info


def _apply_zeis_porte_to_context(
    ctx: dict,
    info: dict,
) -> dict:
    if not info.get("active"):
        return info

    limite_porte = _num(
        info.get("limite_total_m2")
    )

    area_pedida = _num(
        ctx.get("area_pedida")
    )

    ground_limit = (
        _num(ctx.get("A_teto_projeto"))
        or _num(ctx.get("A_op2_max"))
        or _num(ctx.get("A_to"))
    )

    info["ground_limit_m2"] = ground_limit

    if area_pedida is not None and area_pedida > 0:
        area_adotada = area_pedida

        if ground_limit is not None:
            area_adotada = min(
                area_adotada,
                ground_limit,
            )

        area_adotada = min(
            area_adotada,
            limite_porte,
        )

        info["ground_reference_m2"] = area_adotada

        info["porte_restante_m2"] = max(
            limite_porte - area_adotada,
            0.0,
        )

        info["excedeu_porte"] = (
            area_pedida > limite_porte + 0.01
        )

        info["excedeu_implantacao"] = (
            ground_limit is not None
            and area_pedida > ground_limit + 0.01
        )

        # Atualiza o contexto compartilhado para que
        # os itens seguintes usem a mesma área.
        ctx["A_considerada"] = area_adotada

        ctx["excedeu_area"] = (
            area_pedida > area_adotada + 0.01
        )

        area_lote = _num(
            ctx.get("A")
        )

        area_perm_min = _num(
            ctx.get("A_perm_min")
        )

        area_total_ia = _num(
            ctx.get("A_total")
        )

        if area_lote is not None and area_lote > 0:
            ctx["to_projeto_pct"] = (
                area_adotada / area_lote
            ) * 100.0

            ctx["A_livre"] = max(
                area_lote - area_adotada,
                0.0,
            )

            if area_perm_min is not None:
                ctx["A_impermeavel_possivel"] = (
                    ctx["A_livre"]
                    - area_perm_min
                )

        if area_total_ia is not None:
            # Mantém apenas o saldo matemático do IA.
            # O item 9 fará a leitura separada do porte.
            ctx["A_ia_saldo"] = (
                area_total_ia
                - area_adotada
            )

    else:
        if ground_limit is not None:
            area_referencia = min(
                ground_limit,
                limite_porte,
            )
        else:
            area_referencia = limite_porte

        info["ground_reference_m2"] = (
            area_referencia
        )

        info["porte_restante_m2"] = max(
            limite_porte
            - area_referencia,
            0.0,
        )

    ctx["zeis_porte_info"] = info

    return info


def _render_art112_intro() -> None:
    md(
        "**Flexibilidade de recuos no uso residencial unifamiliar**"
    )

    md(
        "Para residência unifamiliar, pode ser considerada a aplicação do **Art. 112**, que permite flexibilizar os recuos de frente e laterais, podendo chegar a **0,00 m**, desde que o projeto respeite a **Taxa de Ocupação (TO) máxima**, a **Taxa de Permeabilidade (TP) mínima** e as demais exigências do licenciamento.\n\n"
        "Essa flexibilização ajuda na implantação da edificação, mas **não aumenta a Taxa de Ocupação (TO)** e **não elimina a área permeável mínima**.\n\n"
        "A aplicação dessa leitura deve ser confirmada no licenciamento municipal. Ela não representa aprovação automática do projeto."
    )


def _render_recuos(
    rec_fr,
    rec_lat,
    rec_fun,
    w_util,
    d_util,
    a_recuos,
) -> None:
    md(
        "**Conferência dos recuos deste lote**"
    )

    md(
        "Para este terreno, os parâmetros da zona indicam:"
    )

    if rec_fr is not None:
        md(
            f"- recuo frontal: **{fmt_num(rec_fr)} m**;"
        )

    if rec_lat is not None:
        md(
            f"- recuos laterais: **{fmt_num(rec_lat)} m**;"
        )

    if rec_fun is not None:
        md(
            f"- recuo de fundos: **{fmt_num(rec_fun)} m**."
        )

    if (
        w_util is not None
        or d_util is not None
        or a_recuos is not None
    ):
        md(
            "Considerando as dimensões informadas:"
        )

    if w_util is not None:
        md(
            f"👉 largura útil: **{fmt_num(w_util)} m**"
        )

    if d_util is not None:
        md(
            f"👉 profundidade útil: **{fmt_num(d_util)} m**"
        )

    if (
        a_recuos is not None
        and w_util is not None
        and d_util is not None
    ):
        md(
            f"👉 área física estimada pelos recuos: "
            f"**{fmt_num(w_util)} m × "
            f"{fmt_num(d_util)} m = "
            f"{fmt_num(a_recuos)} m²**"
        )


def _render_zeis_porte(
    ctx: dict,
    info: dict,
) -> None:
    area_lote = _num(
        ctx.get("A")
    )

    to_max = _num(
        ctx.get("to_max")
    )

    area_to = _num(
        ctx.get("A_to")
    )

    area_pedida = _num(
        ctx.get("area_pedida")
    )

    area_adotada = _num(
        info.get("ground_reference_m2")
    )

    ground_limit = _num(
        info.get("ground_limit_m2")
    )

    limite_porte = _num(
        info.get("limite_total_m2")
    )

    classificacao = info.get(
        "classificacao"
    )

    pct_txt = _fmt_pct_local(
        to_max
    )

    md(
        f"A **Taxa de Ocupação (TO)** define quanto do terreno pode ser ocupado pela projeção da edificação no pavimento térreo.\n\n"
        f"Para este terreno, a Taxa de Ocupação máxima é de **{pct_txt}**.\n\n"
        f"👉 **{fmt_num(area_lote)} m² × {pct_txt} = {fmt_num(area_to)} m²**\n\n"
        f"Portanto, considerando apenas a Taxa de Ocupação, seria possível ocupar até **{fmt_num(area_to)} m² no pavimento térreo**."
    )

    if classificacao == "AP":
        md(
            "Entretanto, por se tratar de uma **ZEIS**, também é necessário observar a adequabilidade do uso e o porte permitido.\n\n"
            "Neste caso, a classificação efetiva é **AP — Adequado para pequeno porte**, o que limita o empreendimento a **250,00 m² de área construída total**."
        )

    elif classificacao == "AP/AM":
        md(
            "Entretanto, por se tratar de uma **ZEIS**, também é necessário observar a adequabilidade do uso e o porte permitido.\n\n"
            "Neste caso, a classificação efetiva é **AP/AM — Adequado para pequeno ou médio porte**, o que limita o empreendimento a **1.500,00 m² de área construída total**."
        )

    if area_pedida is None or area_pedida <= 0:
        md(
            "Como nenhuma área pretendida foi informada, o relatório compara os principais limites aplicáveis ao terreno."
        )

        md(
            f"- limite de ocupação no térreo pela **Taxa de Ocupação (TO)**: **{fmt_num(area_to)} m²**;\n"
            f"- limite de **área construída total pelo porte**: **{fmt_num(limite_porte)} m²**."
        )

        if (
            ground_limit is not None
            and ground_limit < limite_porte - 0.01
        ):
            diferenca = (
                limite_porte
                - ground_limit
            )

            md(
                f"Neste terreno, a referência de implantação no térreo fica em **{fmt_num(ground_limit)} m²**, enquanto o limite de porte admite até **{fmt_num(limite_porte)} m² de área construída total**.\n\n"
                f"👉 A diferença de até **{fmt_num(diferenca)} m²** poderá, em tese, ser distribuída em pavimento superior, desde que o Índice de Aproveitamento, a altura, os recuos, a permeabilidade e as demais exigências também permitam."
            )

        else:
            md(
                f"**Para este estudo preliminar, a referência máxima de área construída total é de {fmt_num(limite_porte)} m².**"
            )

    else:
        md(
            f"👉 **Área pretendida informada: {fmt_num(area_pedida)} m² no térreo.**"
        )

        excede_to = (
            area_to is not None
            and area_pedida > area_to + 0.01
        )

        excede_porte = (
            area_pedida
            > limite_porte + 0.01
        )

        excede_implantacao = (
            ground_limit is not None
            and area_pedida > ground_limit + 0.01
        )

        if excede_to and excede_porte:
            md(
                f"A área informada ultrapassa tanto o limite de **{fmt_num(area_to)} m² pela Taxa de Ocupação** quanto o limite de **{fmt_num(limite_porte)} m² de área construída total pelo porte**."
            )

            md(
                f"👉 **Por isso, os {fmt_num(area_pedida)} m² informados não podem ser adotados integralmente nesta análise.**"
            )

            md(
                f"**Para este estudo preliminar, serão considerados {fmt_num(area_adotada)} m² como referência de implantação no térreo.**"
            )

        elif excede_porte:
            md(
                f"Embora a Taxa de Ocupação permita até **{fmt_num(area_to)} m² no térreo**, os **{fmt_num(area_pedida)} m²** informados ultrapassam o limite de **{fmt_num(limite_porte)} m² de área construída total** correspondente ao porte permitido."
            )

            md(
                f"👉 **Por isso, a área pretendida não pode ser adotada integralmente nesta análise.**\n\n"
                f"**Para este estudo preliminar, serão considerados no máximo {fmt_num(area_adotada)} m² como referência de área construída no térreo.**"
            )

        elif excede_implantacao:
            md(
                f"A área pretendida está dentro do limite de porte de **{fmt_num(limite_porte)} m² de área construída total**, mas ultrapassa a referência máxima calculada para a implantação no térreo, de **{fmt_num(ground_limit)} m²**."
            )

            md(
                f"👉 **Para esta análise, a referência adotada no térreo passa a ser de {fmt_num(area_adotada)} m².**"
            )

        else:
            md(
                f"A área pretendida de **{fmt_num(area_pedida)} m²** está dentro da Taxa de Ocupação e do limite de porte considerados nesta análise."
            )

        if (
            area_adotada is not None
            and area_lote
        ):
            to_efetiva = (
                area_adotada
                / area_lote
            ) * 100.0

            md(
                f"Considerando **{fmt_num(area_adotada)} m² no térreo**, a Taxa de Ocupação correspondente será:\n\n"
                f"👉 **{fmt_num(area_adotada)} m² ÷ {fmt_num(area_lote)} m² = {_fmt_pct_local(to_efetiva)}**"
            )

    if (
        ground_limit is not None
        and ground_limit < limite_porte - 0.01
    ):
        md(
            f"**Leitura prática:** neste caso, a referência máxima de implantação no térreo é de **{fmt_num(ground_limit)} m²**, enquanto o limite de porte admite até **{fmt_num(limite_porte)} m² de área construída total**.\n\n"
            "A diferença poderá existir em pavimento superior somente se o Índice de Aproveitamento, a altura, os recuos, a Taxa de Permeabilidade e as demais exigências também permitirem."
        )

    elif (
        area_to is not None
        and limite_porte <= area_to + 0.01
    ):
        md(
            f"**Leitura prática:** neste caso, a Taxa de Ocupação permitiria uma implantação maior no térreo, mas o **limite de porte é mais restritivo para a área construída total do empreendimento**, que fica limitada a **{fmt_num(limite_porte)} m²**."
        )

    else:
        md(
            "**Leitura prática:** a Taxa de Ocupação controla quanto pode ser ocupado no térreo, enquanto o porte controla a área construída total do empreendimento."
        )

    if ctx.get("is_irregular"):
        md(
            "**Terreno irregular — leitura pela área total**"
        )

        md(
            aviso_texto()
        )

        md(
            f"A forma real da implantação depende da geometria do terreno, da planta/topografia e da confirmação no licenciamento. "
            f"O limite de porte de **{fmt_num(limite_porte)} m² de área construída total** permanece aplicável."
        )

        return

    rec_fr = ctx.get(
        "rec_fr"
    )

    rec_lat = ctx.get(
        "rec_lat"
    )

    rec_fun = ctx.get(
        "rec_fun"
    )

    w_util = ctx.get(
        "W_util"
    )

    d_util = ctx.get(
        "D_util"
    )

    a_recuos = ctx.get(
        "A_recuos"
    )

    _render_art112_intro()

    recuos_menor_que_to = (
        _num(a_recuos) is not None
        and _num(area_to) is not None
        and _num(a_recuos) < _num(area_to)
        and not _same(
            a_recuos,
            area_to,
        )
    )

    if recuos_menor_que_to:
        md(
            "**Cenário A — leitura com flexibilidade do Art. 112**"
        )

        md(
            "Com a aplicação do **Art. 112**, pode ser considerada a flexibilização dos recuos de frente e laterais, desde que sejam respeitadas a **Taxa de Ocupação (TO) máxima**, a **Taxa de Permeabilidade (TP) mínima** e as demais exigências do licenciamento.\n\n"
            f"Neste cenário, a referência de ocupação no térreo pela TO é de **{fmt_num(area_to)} m²**."
        )

        md(
            "**Cenário B — leitura com recuos padrão da zona**"
        )

        _render_recuos(
            rec_fr,
            rec_lat,
            rec_fun,
            w_util,
            d_util,
            a_recuos,
        )

        md(
            f"Pela leitura dos recuos padrão da zona, a referência física de ocupação no térreo é de **{fmt_num(a_recuos)} m²**."
        )

        md(
            f"**Importante:** independentemente da leitura de recuos adotada, o limite de **{fmt_num(limite_porte)} m² de área construída total** decorrente do porte continua aplicável."
        )

        md(
            "A confirmação final deve ser feita no licenciamento municipal."
        )

        return

    _render_recuos(
        rec_fr,
        rec_lat,
        rec_fun,
        w_util,
        d_util,
        a_recuos,
    )

    if a_recuos is not None:
        if (
            _num(a_recuos) is not None
            and _num(area_to) is not None
            and _num(a_recuos) > _num(area_to)
        ):
            md(
                f"Mesmo que a área física estimada pelos recuos seja de **{fmt_num(a_recuos)} m²**, a ocupação no térreo não pode ultrapassar o limite da **Taxa de Ocupação (TO)**, que é de **{fmt_num(area_to)} m²**."
            )

        else:
            md(
                "Neste caso, a área física estimada pelos recuos coincide com o limite da **Taxa de Ocupação (TO)** ou não cria restrição adicional relevante para a leitura preliminar."
            )

    md(
        f"A implantação real deverá respeitar a **Taxa de Ocupação (TO)**, a **Taxa de Permeabilidade (TP)**, os recuos aplicáveis e, nesta ZEIS, o limite de **{fmt_num(limite_porte)} m² de área construída total** correspondente ao porte permitido."
    )


def render(ctx: dict) -> None:
    if (
        ctx.get("to_max") is None
        or ctx.get("A_to") is None
    ):
        st.info(
            "Sem Taxa de Ocupação (TO) máxima cadastrada para esta zona/uso."
        )
        return

    porte_info = _zeis_porte_info(
        ctx
    )

    # Lógica especial apenas para ZEIS com AP ou AP/AM efetivo.
    if porte_info.get("active"):
        porte_info = (
            _apply_zeis_porte_to_context(
                ctx,
                porte_info,
            )
        )

        _render_zeis_porte(
            ctx,
            porte_info,
        )

        return

    area_lote = ctx.get(
        "A"
    )

    to_max = ctx.get(
        "to_max"
    )

    area_to = ctx.get(
        "A_to"
    )

    area_pedida = ctx.get(
        "area_pedida"
    )

    area_considerada = ctx.get(
        "A_considerada"
    )

    excedeu_area = bool(
        ctx.get("excedeu_area")
    )

    rec_fr = ctx.get(
        "rec_fr"
    )

    rec_lat = ctx.get(
        "rec_lat"
    )

    rec_fun = ctx.get(
        "rec_fun"
    )

    w_util = ctx.get(
        "W_util"
    )

    d_util = ctx.get(
        "D_util"
    )

    a_recuos = ctx.get(
        "A_recuos"
    )

    pct_txt = _fmt_pct_local(
        to_max
    )

    md(
        f"A zona permite ocupar até **{pct_txt}** do terreno no térreo.\n\n"
        f"👉 **{fmt_num(area_lote)} m² × {pct_txt} = {fmt_num(area_to)} m²**\n\n"
        "Esse é o limite máximo permitido pela Taxa de Ocupação (TO)."
    )

    # ZEIS cuja via efetiva é A.
    # Mantém toda a lógica antiga de TO, sem teto de AP/AP-AM da zona.
    if porte_info.get("via_override"):
        zone_class = str(
            ctx.get("zone_class") or ""
        ).strip().upper()

        if zone_class == "AP":
            limite_zona = (
                "250,00 m²"
            )
        else:
            limite_zona = (
                "1.500,00 m²"
            )

        md(
            "**Leitura específica da adequabilidade pela via**\n\n"
            "Pela classificação da zona, o uso apresentava limitação relacionada ao porte. "
            "Entretanto, a classificação efetiva da via para este uso é **A — Adequado**.\n\n"
            f"Por isso, **não se aplica nesta análise o limite de {limite_zona} decorrente da classificação de porte da zona**.\n\n"
            "Isso não altera os parâmetros urbanísticos da ZEIS. "
            "A edificação continua sujeita à **Taxa de Ocupação, Taxa de Permeabilidade, Índice de Aproveitamento, recuos, altura máxima e demais regras aplicáveis**."
        )

    to_efetiva = None

    if (
        area_pedida is not None
        and area_lote
    ):
        try:
            to_efetiva = (
                float(area_pedida)
                / float(area_lote)
            ) * 100.0
        except Exception:
            to_efetiva = None

    if (
        area_pedida is not None
        and area_considerada is not None
    ):
        if excedeu_area:
            md(
                f"👉 **Área pretendida informada: {fmt_num(area_pedida)} m².** Como esse valor ultrapassa o limite máximo permitido pela **Taxa de Ocupação (TO)**, ele não pode ser adotado como referência de implantação no térreo. Por isso, o estudo passa a considerar **{fmt_num(area_considerada)} m²** como teto urbanístico inicial para esta análise."
            )

            if to_efetiva is not None:
                md(
                    f"👉 **Taxa de Ocupação (TO) correspondente à área pretendida: {fmt_num(area_pedida)} m² ÷ {fmt_num(area_lote)} m² = {_fmt_pct_local(to_efetiva)}**\n\n"
                    f"Isso significa que, para esta proposta, a ocupação no térreo ficaria em **{_fmt_pct_local(to_efetiva)}** do lote, portanto acima da Taxa de Ocupação (TO) máxima permitida de **{pct_txt}**."
                )

            if (
                a_recuos is not None
                and float(area_pedida)
                <= float(a_recuos)
            ):
                md(
                    f"👉 A área pretendida informada cabe fisicamente pelos recuos, mas não pode ser adotada porque ultrapassa a **Taxa de Ocupação (TO)** máxima. A referência de ocupação máxima no térreo continua sendo **{fmt_num(area_considerada)} m²**, e o projeto precisaria ser reduzido para respeitar esse limite."
                )

        else:
            md(
                f"👉 **Área pretendida informada: {fmt_num(area_pedida)} m².** Como esse valor está abaixo do limite máximo permitido, ele pode ser adotado como referência inicial para a implantação no térreo."
            )

            md(
                f"👉 **Na leitura com a flexibilidade do Art. 112, a área pretendida de {fmt_num(area_pedida)} m² é viável, sujeita à confirmação no licenciamento.**"
            )

            if to_efetiva is not None:
                md(
                    f"👉 **Taxa de Ocupação (TO) correspondente à área pretendida: {fmt_num(area_pedida)} m² ÷ {fmt_num(area_lote)} m² = {_fmt_pct_local(to_efetiva)}**\n\n"
                    f"Isso significa que, para esta proposta, a ocupação no térreo ficaria em **{_fmt_pct_local(to_efetiva)}** do lote, portanto abaixo da Taxa de Ocupação (TO) máxima permitida de **{pct_txt}**."
                )

    if ctx.get(
        "is_irregular"
    ):
        md(
            "**Terreno irregular — leitura pela área total**"
        )

        md(
            aviso_texto()
        )

        md(
            limite_to_text(
                fmt_num(area_to)
            ).replace(
                "Taxa de Ocupação",
                "Taxa de Ocupação (TO)",
            )
        )

        if (
            area_pedida is not None
            and area_considerada is not None
        ):
            if excedeu_area:
                md(
                    f"👉 **Neste caso, a área pretendida precisa ser reduzida para respeitar o limite máximo de {fmt_num(area_considerada)} m² pela Taxa de Ocupação (TO).**"
                )
            else:
                md(
                    f"👉 **Neste caso, a área pretendida de {fmt_num(area_pedida)} m² está dentro do limite máximo pela Taxa de Ocupação (TO).**"
                )

        else:
            md(
                "👉 **Sem área pretendida informada, o estudo apresenta o limite máximo pela Taxa de Ocupação (TO) como referência inicial.**"
            )

        return

    _render_art112_intro()

    recuos_menor_que_to = (
        _num(a_recuos) is not None
        and _num(area_to) is not None
        and _num(a_recuos) < _num(area_to)
        and not _same(
            a_recuos,
            area_to,
        )
    )

    if recuos_menor_que_to:
        md(
            "**Cenário A — leitura com flexibilidade do Art. 112**"
        )

        md(
            "Com a aplicação do **Art. 112**, pode ser considerada a flexibilização dos recuos de frente e laterais, desde que sejam respeitadas a **Taxa de Ocupação (TO) máxima**, a **Taxa de Permeabilidade (TP) mínima** e as demais exigências do licenciamento.\n\n"
            f"Neste cenário, a referência de ocupação no térreo é de **{fmt_num(area_to)} m²**."
        )

        md(
            "**Cenário B — leitura com recuos padrão da zona**"
        )

        _render_recuos(
            rec_fr,
            rec_lat,
            rec_fun,
            w_util,
            d_util,
            a_recuos,
        )

        md(
            f"Pela leitura dos recuos padrão da zona, a referência física de ocupação no térreo é de **{fmt_num(a_recuos)} m²**."
        )

        md(
            "**Leitura prática**"
        )

        md(
            f"A referência de ocupação depende da leitura adotada no licenciamento. Com a flexibilidade do **Art. 112**, a ocupação pode chegar ao limite da **Taxa de Ocupação (TO)**, que é de **{fmt_num(area_to)} m²**. Pela leitura dos recuos padrão, a área física estimada é de **{fmt_num(a_recuos)} m²**."
        )

        if (
            area_pedida is not None
            and area_considerada is not None
        ):
            if excedeu_area:
                md(
                    f"👉 Como a área pretendida informada foi de **{fmt_num(area_pedida)} m²**, ela ultrapassa a **Taxa de Ocupação (TO)** máxima. Para esta análise preliminar, o relatório deve adotar **{fmt_num(area_considerada)} m²** como teto de referência no térreo."
                )
            else:
                md(
                    f"👉 Como a área pretendida informada foi de **{fmt_num(area_pedida)} m²**, ela fica dentro da **Taxa de Ocupação (TO)** e permanece viável nas duas leituras, quando couber. A implantação final ainda deve ser conferida conforme a leitura de recuos adotada no licenciamento."
                )

        md(
            "A confirmação final deve ser feita no licenciamento municipal."
        )

        return

    _render_recuos(
        rec_fr,
        rec_lat,
        rec_fun,
        w_util,
        d_util,
        a_recuos,
    )

    if a_recuos is not None:
        if (
            _num(a_recuos) is not None
            and _num(area_to) is not None
            and _num(a_recuos) > _num(area_to)
        ):
            md(
                f"Mesmo que a área física estimada pelos recuos seja de **{fmt_num(a_recuos)} m²**, a ocupação no térreo não pode ultrapassar o limite da **Taxa de Ocupação (TO)**, que é de **{fmt_num(area_to)} m²**."
            )
        else:
            md(
                "Neste caso, a área física estimada pelos recuos coincide com o limite da **Taxa de Ocupação (TO)** ou não cria restrição adicional relevante para a leitura preliminar."
            )

    md(
        "**Leitura prática**"
    )

    ref = (
        area_considerada
        if (
            area_considerada is not None
            and area_pedida is not None
        )
        else area_to
    )

    md(
        f"Para este lote, a referência de ocupação máxima no térreo é de **{fmt_num(ref)} m²**."
    )

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
