from __future__ import annotations

import streamlit as st

from .common import md, fmt_num


def _num(value):
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None


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


def _zeis_porte_info(ctx: dict) -> dict:
    existing = ctx.get(
        "zeis_porte_info"
    )

    if isinstance(
        existing,
        dict,
    ):
        return existing

    status = str(
        ctx.get("status_curto")
        or ""
    ).strip().upper()

    zone_class = str(
        ctx.get("zone_class")
        or ""
    ).strip().upper()

    via_class = str(
        ctx.get("via_class")
        or ""
    ).strip().upper()

    is_zeis = (
        _zone_key(ctx)
        .startswith("ZEIS")
    )

    info = {
        "is_zeis": is_zeis,
        "active": False,
        "classificacao": None,
        "limite_total_m2": None,
        "via_override": False,
        "ground_limit_m2": None,
        "ground_reference_m2": None,
    }

    if not is_zeis:
        return info

    # Se a via efetivamente classifica o uso como A,
    # não reaplicar o limite de porte da zona.
    if (
        via_class == "A"
        and zone_class in {"AP", "AP/AM"}
    ):
        info["via_override"] = True
        return info

    if "SOMENTE PEQUENO PORTE" in status:
        info["active"] = True
        info["classificacao"] = "AP"
        info["limite_total_m2"] = 250.0

    elif "PEQUENO OU MÉDIO PORTE" in status:
        info["active"] = True
        info["classificacao"] = "AP/AM"
        info["limite_total_m2"] = 1500.0

    if not info["active"]:
        return info

    area_pedida = _num(
        ctx.get("area_pedida")
    )

    area_considerada = _num(
        ctx.get("A_considerada")
    )

    ground_limit = (
        _num(ctx.get("A_teto_projeto"))
        or _num(ctx.get("A_op2_max"))
        or _num(ctx.get("A_to"))
    )

    limite = info[
        "limite_total_m2"
    ]

    info[
        "ground_limit_m2"
    ] = ground_limit

    if (
        area_pedida is not None
        and area_pedida > 0
    ):
        if area_considerada is not None:
            info[
                "ground_reference_m2"
            ] = min(
                area_considerada,
                limite,
            )

        else:
            ref = area_pedida

            if ground_limit is not None:
                ref = min(
                    ref,
                    ground_limit,
                )

            info[
                "ground_reference_m2"
            ] = min(
                ref,
                limite,
            )

    else:
        if ground_limit is not None:
            info[
                "ground_reference_m2"
            ] = min(
                ground_limit,
                limite,
            )

        else:
            info[
                "ground_reference_m2"
            ] = limite

    return info


def _render_exemplo_padrao(
    classificacao: str,
    limite_porte: float,
    ground_limit,
) -> None:
    """
    Exemplo didático.

    AP:
        150 + 100 = 250 m².

    AP/AM:
        900 + 600 = 1.500 m².

    Se o próprio terreno não comportar esse valor de térreo,
    o exemplo é reduzido para não apresentar uma implantação
    incompatível com a referência calculada.
    """

    if classificacao == "AP":
        exemplo_terreo = 150.0

    else:
        exemplo_terreo = 900.0

    if ground_limit is not None:
        exemplo_terreo = min(
            exemplo_terreo,
            ground_limit,
        )

    exemplo_terreo = min(
        exemplo_terreo,
        limite_porte,
    )

    restante = max(
        limite_porte
        - exemplo_terreo,
        0.0,
    )

    md(
        "**Exemplo para entender melhor:**"
    )

    if classificacao == "AP":
        if (
            abs(
                exemplo_terreo
                - 150.0
            ) <= 0.01
        ):
            md(
                "Imagine que o projeto utilizasse apenas **150,00 m² no térreo**."
            )
        else:
            md(
                f"Considerando a referência de ocupação deste terreno, imagine uma solução com **{fmt_num(exemplo_terreo)} m² no térreo**."
            )

    else:
        if (
            abs(
                exemplo_terreo
                - 900.0
            ) <= 0.01
        ):
            md(
                "Imagine que o projeto utilizasse **900,00 m² no térreo**."
            )
        else:
            md(
                f"Considerando a referência de ocupação deste terreno, imagine uma solução com **{fmt_num(exemplo_terreo)} m² no térreo**."
            )

    md(
        f"Nesse caso, ainda poderiam existir:\n\n"
        f"👉 **{fmt_num(limite_porte)} m² − {fmt_num(exemplo_terreo)} m² = {fmt_num(restante)} m²**\n\n"
        "de área construída dentro do limite de porte."
    )

    if restante > 0.01:
        md(
            f"Por exemplo:\n\n"
            f"👉 **{fmt_num(exemplo_terreo)} m² no térreo + até {fmt_num(restante)} m² em pavimentos superiores = {fmt_num(limite_porte)} m² de área construída total**"
        )

    md(
        "Essa distribuição é apenas ilustrativa. A solução real dependerá também do **Índice de Aproveitamento, da altura máxima, dos recuos, da Taxa de Permeabilidade e das demais exigências aplicáveis**."
    )


def _render_zeis_ia(
    ctx: dict,
    info: dict,
) -> None:
    area_lote = _num(
        ctx.get("A")
    )

    ia_max = _num(
        ctx.get("ia_max")
    )

    total_ia = _num(
        ctx.get("A_total")
    )

    area_pedida = _num(
        ctx.get("area_pedida")
    )

    area_terreo = _num(
        info.get(
            "ground_reference_m2"
        )
    )

    ground_limit = _num(
        info.get(
            "ground_limit_m2"
        )
    )

    limite_porte = _num(
        info.get(
            "limite_total_m2"
        )
    )

    classificacao = info.get(
        "classificacao"
    )

    md(
        "O **Índice de Aproveitamento (IA)** indica o potencial construtivo do terreno a partir da área do lote e do índice máximo previsto para a zona.\n\n"
        f"Neste caso:\n\n"
        f"👉 **{fmt_num(area_lote)} m² × {fmt_num(ia_max)} = {fmt_num(total_ia)} m²**\n\n"
        f"Portanto, o terreno apresenta um potencial matemático de **{fmt_num(total_ia)} m² pelo Índice de Aproveitamento (IA)**."
    )

    md(
        "Esse valor, porém, **não representa automaticamente a área que poderá ser construída**. "
        "O Índice de Aproveitamento e o enquadramento pelo porte são parâmetros diferentes e precisam ser analisados em conjunto."
    )

    if classificacao == "AP":
        md(
            "Para este uso em ZEIS, a classificação efetiva é **AP — Adequado para pequeno porte**, limitando o empreendimento a **250,00 m² de área construída total**."
        )

    elif classificacao == "AP/AM":
        md(
            "Para este uso em ZEIS, a classificação efetiva é **AP/AM — Adequado para pequeno ou médio porte**, limitando o empreendimento a **1.500,00 m² de área construída total**."
        )

    md(
        "Assim, mesmo que o Índice de Aproveitamento indique um potencial superior, esse potencial **não elimina o limite de área construída decorrente do porte**."
    )

    if (
        area_pedida is not None
        and area_pedida > 0
        and area_terreo is not None
    ):
        restante_porte = max(
            limite_porte
            - area_terreo,
            0.0,
        )

        if restante_porte <= 0.01:
            md(
                f"Como esta análise já considera **{fmt_num(area_terreo)} m²**, o limite de porte foi integralmente utilizado."
            )

            md(
                f"👉 **Não é possível acrescentar nova área construída considerada para o enquadramento do porte sem ultrapassar os {fmt_num(limite_porte)} m² permitidos.**"
            )

            _render_exemplo_padrao(
                classificacao,
                limite_porte,
                ground_limit,
            )

        else:
            md(
                f"Como esta análise considera **{fmt_num(area_terreo)} m² no térreo**, ainda existe margem dentro do limite de porte:"
            )

            md(
                f"👉 **{fmt_num(limite_porte)} m² − {fmt_num(area_terreo)} m² = {fmt_num(restante_porte)} m²**"
            )

            md(
                f"**Até {fmt_num(restante_porte)} m² adicionais de área construída poderiam existir dentro do limite de porte.**"
            )

            md(
                "**Exemplo para entender melhor:**"
            )

            md(
                f"👉 **{fmt_num(area_terreo)} m² no térreo + até {fmt_num(restante_porte)} m² em pavimentos superiores = {fmt_num(limite_porte)} m² de área construída total**"
            )

            md(
                "Essa distribuição é apenas ilustrativa. A solução real depende também do **Índice de Aproveitamento, da altura máxima, dos recuos, da Taxa de Permeabilidade e das demais exigências aplicáveis**."
            )

    else:
        md(
            "Como nenhuma área pretendida foi informada, o exemplo abaixo serve apenas para explicar como o limite de porte pode ser distribuído entre o térreo e outros pavimentos."
        )

        _render_exemplo_padrao(
            classificacao,
            limite_porte,
            ground_limit,
        )

    md(
        f"**Leitura final:** embora o Índice de Aproveitamento indique um potencial matemático de **{fmt_num(total_ia)} m²**, a área construída total nesta condição permanece limitada a **{fmt_num(limite_porte)} m²** pelo porte permitido."
    )


def render(ctx: dict) -> None:
    porte_info = _zeis_porte_info(
        ctx
    )

    if (
        ctx["ia_max"] is None
        or ctx["A_total"] is None
    ):
        st.info(
            "Sem Índice de Aproveitamento (IA) máximo cadastrado para esta zona/uso."
        )

    elif porte_info.get(
        "active"
    ):
        _render_zeis_ia(
            ctx,
            porte_info,
        )

    else:
        # Fora de ZEIS ou quando não há limite AP/AP-AM efetivo,
        # preserva o comportamento anterior.
        md(
            f"Além da ocupação no térreo, a zona também define o potencial construtivo total do lote por meio do **Índice de Aproveitamento (IA)**.\n\n"
            f"Se o **Índice de Aproveitamento (IA)** máximo da zona for **{fmt_num(ctx['ia_max'])}**, então o potencial construtivo total do lote será:\n\n"
            f"👉 **{fmt_num(ctx['A'])} m² × {fmt_num(ctx['ia_max'])} = {fmt_num(ctx['A_total'])} m²**\n\n"
            f"Esse é o total que pode ser distribuído entre térreo e pavimentos superiores, respeitando também os demais parâmetros urbanísticos."
        )

        if porte_info.get(
            "via_override"
        ):
            md(
                "**Leitura específica da adequabilidade pela via:** neste caso, a classificação efetiva da via para o uso é **A — Adequado**.\n\n"
                "Por isso, não é aplicado o limite de pequeno ou médio porte decorrente da classificação original da zona.\n\n"
                "O **Índice de Aproveitamento da ZEIS permanece aplicável**, assim como a Taxa de Ocupação, a Taxa de Permeabilidade, os recuos, a altura máxima e os demais parâmetros urbanísticos."
            )

        if (
            ctx["A_considerada"]
            is not None
            and ctx["A_ia_saldo"]
            is not None
        ):
            md(
                f"Como o relatório adotou **{fmt_num(ctx['A_considerada'])} m²** no térreo, o saldo estimado para crescer acima fica assim:\n\n"
                f"👉 **{fmt_num(ctx['A_total'])} m² − {fmt_num(ctx['A_considerada'])} m² = {fmt_num(ctx['A_ia_saldo'])} m²**\n\n"
                f"**Saldo estimado para pavimentos superiores: {fmt_num(ctx['A_ia_saldo'])} m²**"
            )

            md(
                f"👉 **Leitura prática:** considerando a área adotada de **{fmt_num(ctx['A_considerada'])} m²** no térreo, ainda restam **{fmt_num(ctx['A_ia_saldo'])} m²** de potencial construtivo pelo **Índice de Aproveitamento (IA)** para crescimento em pavimentos superiores, desde que o projeto respeite também altura máxima, recuos, ventilação, iluminação, circulação e demais exigências aplicáveis."
            )

    if (
        ctx["gabarito_m"]
        is not None
    ):
        md(
            f"**Altura máxima da zona:** {fmt_num(ctx['gabarito_m'])} m"
        )

        md(
            f"A altura máxima de **{fmt_num(ctx['gabarito_m'])} m** é um parâmetro geral da zona. Isso não significa autorização automática para uma residência unifamiliar atingir essa altura ou construir muitos pavimentos.\n\n"
            "No caso de uma residência unifamiliar, a altura real da edificação depende do projeto arquitetônico, da implantação no lote, da **Taxa de Ocupação (TO)**, da **Taxa de Permeabilidade (TP)**, dos recuos, do **Índice de Aproveitamento (IA)**, das normas técnicas aplicáveis e da confirmação no licenciamento municipal.\n\n"
            "👉 **Na prática:** para este estudo preliminar, a altura da zona serve como limite urbanístico geral, mas a quantidade real de pavimentos deve ser definida e aprovada no projeto."
        )
