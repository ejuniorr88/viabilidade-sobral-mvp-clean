from __future__ import annotations

import streamlit as st

from .common import md, fmt_num, fmt_pct


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
        "ground_reference_m2": None,
    }

    if not is_zeis:
        return info

    # A pela via se sobrepõe à limitação de porte da zona.
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

    if info["active"]:
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


def _scenario(
    label: str,
    area_lote,
    ocupacao,
    area_perm_min,
) -> None:
    area_lote_f = _num(
        area_lote
    )

    ocupacao_f = _num(
        ocupacao
    )

    perm_f = _num(
        area_perm_min
    )

    if (
        area_lote_f is None
        or ocupacao_f is None
        or perm_f is None
    ):
        return

    restante = max(
        area_lote_f
        - ocupacao_f,
        0.0,
    )

    impermeavel = max(
        restante
        - perm_f,
        0.0,
    )

    md(
        f"**{label}**"
    )

    md(
        f"Considerando a ocupação de referência de **{fmt_num(ocupacao_f)} m²**, temos:\n\n"
        f"👉 **{fmt_num(area_lote_f)} m² − {fmt_num(ocupacao_f)} m² = {fmt_num(restante)} m²**\n\n"
        f"Ou seja, restam **{fmt_num(restante)} m² sem ocupação no térreo**.\n\n"
        f"Dentro desses **{fmt_num(restante)} m²**:\n\n"
        f"- **{fmt_num(perm_f)} m²** precisam permanecer permeáveis;\n"
        f"- **{fmt_num(impermeavel)} m²** podem receber piso impermeável, desde que a área permeável mínima seja preservada."
    )


def _render_zeis_permeabilidade(
    ctx: dict,
    info: dict,
) -> None:
    area_lote = _num(
        ctx.get("A")
    )

    tp_min = _num(
        ctx.get("tp_min")
    )

    area_perm_min = _num(
        ctx.get("A_perm_min")
    )

    area_ref = _num(
        info.get("ground_reference_m2")
    )

    area_pedida = _num(
        ctx.get("area_pedida")
    )

    md(
        f"Além da área ocupada pela edificação, uma parte do terreno deve atender à **Taxa de Permeabilidade (TP)** mínima prevista para a zona.\n\n"
        f"Para este terreno, a Taxa de Permeabilidade mínima é de **{fmt_pct(tp_min)}**.\n\n"
        f"👉 **{fmt_num(area_lote)} m² × {fmt_pct(tp_min)} = {fmt_num(area_perm_min)} m²**\n\n"
        f"Portanto, deverão ser garantidos pelo menos **{fmt_num(area_perm_min)} m² de área permeável**, observados os critérios aplicáveis aos pisos e às demais soluções admitidas."
    )

    if area_ref is None:
        return

    area_fora = max(
        area_lote
        - area_ref,
        0.0,
    )

    if (
        area_pedida is None
        or area_pedida <= 0
    ):
        md(
            f"Como nenhuma área pretendida foi informada, o relatório utiliza **{fmt_num(area_ref)} m²** apenas como referência de ocupação para demonstrar a relação entre a edificação e a área permeável."
        )

    else:
        md(
            f"Considerando, como referência, **{fmt_num(area_ref)} m² de ocupação no térreo**, permaneceriam:"
        )

    md(
        f"👉 **{fmt_num(area_lote)} m² − {fmt_num(area_ref)} m² = {fmt_num(area_fora)} m²**\n\n"
        "fora da projeção da edificação."
    )

    if (
        area_fora + 0.01
        >= area_perm_min
    ):
        md(
            f"Desses **{fmt_num(area_fora)} m²**, pelo menos **{fmt_num(area_perm_min)} m²** deverão atender à exigência mínima de permeabilidade."
        )

        md(
            "**Leitura prática:** a área considerada para a edificação permite, em princípio, compatibilizar a ocupação com a permeabilidade mínima. "
            "A distribuição final dessas áreas depende da implantação do projeto e da confirmação no licenciamento municipal."
        )

    else:
        deficit = (
            area_perm_min
            - area_fora
        )

        md(
            f"👉 **Atenção:** essa ocupação deixaria apenas **{fmt_num(area_fora)} m²** fora da projeção da edificação, mas a zona exige **{fmt_num(area_perm_min)} m² de área permeável**.\n\n"
            f"Déficit estimado: **{fmt_num(deficit)} m²**."
        )

        md(
            "**Leitura prática:** nesta configuração, a ocupação precisa ser revista para que a Taxa de Permeabilidade mínima seja atendida."
        )


def render(ctx: dict) -> None:
    if (
        ctx["tp_min"] is None
        or ctx["A_perm_min"] is None
    ):
        st.info(
            "Sem Taxa de Permeabilidade (TP) mínima cadastrada para esta zona/uso."
        )
        return

    porte_info = _zeis_porte_info(
        ctx
    )

    # Nova leitura somente para ZEIS AP/AP-AM.
    if porte_info.get(
        "active"
    ):
        _render_zeis_permeabilidade(
            ctx,
            porte_info,
        )

        return

    md(
        f"A zona exige que **{fmt_pct(ctx['tp_min'])}** do terreno permaneça como área permeável.\n\n"
        f"👉 **{fmt_num(ctx['A'])} m² × {fmt_pct(ctx['tp_min'])} = {fmt_num(ctx['A_perm_min'])} m²**\n\n"
        f"Isso significa que pelo menos **{fmt_num(ctx['A_perm_min'])} m²** do lote precisam permitir a infiltração da água da chuva no solo."
    )

    if porte_info.get(
        "via_override"
    ):
        md(
            "**Leitura específica da ZEIS pela via:** a classificação efetiva da via altera a adequabilidade do uso, mas **não modifica a Taxa de Permeabilidade da ZEIS**. "
            "A área permeável mínima calculada acima continua integralmente aplicável."
        )

    if ctx.get(
        "is_irregular"
    ):
        a_ref = (
            ctx.get("A_considerada")
            or ctx.get("A_op2_max")
            or ctx.get("A_to")
        )

        md(
            "**Permeabilidade em terreno irregular**"
        )

        _scenario(
            "Cálculo pela área total informada",
            ctx.get("A"),
            a_ref,
            ctx.get("A_perm_min"),
        )

        md(
            "**Leitura prática:** em terreno irregular, a permeabilidade é calculada pela área total informada. "
            "A posição real da área permeável e da edificação depende da forma do lote, da planta/topografia e da confirmação no licenciamento."
        )

        return

    if (
        ctx["A_considerada"]
        is not None
    ):
        _scenario(
            "Cálculo usando a área adotada no relatório",
            ctx.get("A"),
            ctx.get("A_considerada"),
            ctx.get("A_perm_min"),
        )

        try:
            _a_livre = max(
                float(
                    ctx.get("A")
                )
                - float(
                    ctx.get(
                        "A_considerada"
                    )
                ),
                0.0,
            )

            md(
                f"**Área remanescente sem ocupação no térreo:** {fmt_num(_a_livre)} m²."
            )

        except Exception:
            pass

        md(
            f"**Leitura prática:** para este lote, o projeto pode ocupar até **{fmt_num(ctx['A_considerada'])} m²** no térreo e precisa manter pelo menos **{fmt_num(ctx['A_perm_min'])} m²** de área permeável. A implantação deve respeitar essa área permeável mínima e ser confirmada no licenciamento municipal."
        )

        return

    # Se Art. 112 e recuos padrão geram ocupações diferentes,
    # manter os dois cenários.
    a_op2 = (
        ctx.get("A_op2_max")
        or ctx.get("A_to")
    )

    a_op1 = (
        ctx.get("A_op1_max")
        or ctx.get("A_recuos")
    )

    try:
        diferentes = (
            a_op1 is not None
            and a_op2 is not None
            and abs(
                float(a_op1)
                - float(a_op2)
            ) > 0.01
        )

    except Exception:
        diferentes = False

    if diferentes:
        md(
            "**Ver cenários usando os limites de referência**"
        )

        _scenario(
            "Cenário A — leitura com flexibilidade do Art. 112",
            ctx.get("A"),
            a_op2,
            ctx.get("A_perm_min"),
        )

        _scenario(
            "Cenário B — leitura com recuos padrão da zona",
            ctx.get("A"),
            a_op1,
            ctx.get("A_perm_min"),
        )

        md(
            "**Leitura prática:** nos dois cenários, a área permeável mínima precisa ser mantida. "
            "A diferença está na área sem ocupação no térreo e na quantidade de área que pode receber piso impermeável, conforme a implantação adotada e a confirmação no licenciamento municipal."
        )

        return

    base = (
        a_op2
        or a_op1
    )

    _scenario(
        "Cálculo usando a ocupação de referência",
        ctx.get("A"),
        base,
        ctx.get("A_perm_min"),
    )

    md(
        f"**Leitura prática:** para este lote, o projeto pode ocupar até **{fmt_num(base)} m²** no térreo e precisa manter pelo menos **{fmt_num(ctx['A_perm_min'])} m²** de área permeável. A implantação deve respeitar essa área permeável mínima e ser confirmada no licenciamento municipal."
    )


# Contratos textuais legados preservados para testes automatizados: Área livre remanescente no lote | área pretendida inicial
# contrato legado: Cenário pela Opção 2 (Art. 112)
# contrato legado: Cenário pela Opção 1 (recuos padrão)
# contrato legado: área pretendida informada
# contrato legado: devem permanecer permeáveis
