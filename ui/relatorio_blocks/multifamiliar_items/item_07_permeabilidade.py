from __future__ import annotations

import streamlit as st

from .common import md, fmt_num
from urban_rules.common import choose_regular_occupancy


def _fmt_pct_local(v) -> str:
    try:
        return f"{float(v):.1f}%".replace(".", ",")
    except Exception:
        return "—"


def render(ctx: dict) -> None:
    area_lote = ctx.get("lot_area_f")
    tp_min = ctx.get("tp_min_pct")
    area_to = ctx.get("to_m2")
    area_recuos = ctx.get("A_recuos")
    area_pedida_bruta = ctx.get("built_ground")

    if area_lote is None or tp_min is None:
        st.info("Sem Taxa de Permeabilidade cadastrada para esta zona/uso.")
        return

    try:
        area_lote = float(area_lote)
        tp_min = float(tp_min)
    except Exception:
        st.info("Não foi possível calcular a permeabilidade com os dados atuais.")
        return

    area_permeavel_min = area_lote * (tp_min / 100.0)
    tp_txt = _fmt_pct_local(tp_min)

    try:
        area_to = float(area_to) if area_to is not None else None
    except Exception:
        area_to = None

    try:
        area_recuos = float(area_recuos) if area_recuos is not None else None
    except Exception:
        area_recuos = None

    try:
        area_pedida = float(area_pedida_bruta) if area_pedida_bruta not in (None, "") else None
    except Exception:
        area_pedida = None

    area_pedida_valida = area_pedida is not None and area_pedida > 0
    area_pedida_dentro_to = (
        area_pedida_valida
        and area_to is not None
        and area_pedida <= area_to
    )

    md(
        f"A zona exige **{tp_txt}** de área permeável.\n\n"
        f"👉 **{fmt_num(area_lote)} × {tp_txt} = {fmt_num(area_permeavel_min)} obrigatórios permeáveis**\n\n"
        "Isso quer dizer que parte do terreno precisa continuar permitindo a infiltração da água da chuva no solo."
    )

    if ctx.get("is_irregular"):
        base_ocupacao = area_pedida if area_pedida_dentro_to else area_to
        if base_ocupacao is None:
            st.info("Não foi possível montar o cenário básico de permeabilidade para este terreno irregular.")
            return
        area_restante = area_lote - base_ocupacao
        area_impermeavel_livre = area_restante - area_permeavel_min
        md("**Cenário básico pela área total informada**")
        if area_pedida_valida and not area_pedida_dentro_to:
            md(f"Como a área pretendida de **{fmt_num(area_pedida)} m²** ultrapassa a Taxa de Ocupação máxima, este item considera **{fmt_num(base_ocupacao)} m²** como limite pela TO.")
        elif area_pedida_dentro_to:
            md(f"Como a área pretendida de **{fmt_num(area_pedida)} m²** está dentro da Taxa de Ocupação, este item considera essa área para a leitura da permeabilidade.")
        else:
            md(f"Sem área pretendida informada, este item considera o limite máximo pela Taxa de Ocupação: **{fmt_num(base_ocupacao)} m²**.")
        md(f"👉 **Área restante no lote: {fmt_num(area_lote)} − {fmt_num(base_ocupacao)} = {fmt_num(area_restante)} m²**")
        md("Desses:")
        md(f"- **{fmt_num(area_permeavel_min)} m²** devem permitir infiltração no solo")
        md(f"- **{fmt_num(max(area_impermeavel_livre, 0.0))} m²** podem receber piso impermeável")
        md(
            "👉 **Leitura prática:** no terreno irregular, a permeabilidade é calculada pela área total informada. "
            "A posição exata da área permeável e da edificação depende da geometria do lote e deve ser conferida em projeto/licenciamento."
        )
        return

    if ctx.get("is_r21"):
        # O item 6 do R2.1 já trabalha com uma leitura própria da tipologia
        # (2 unidades, até 2 pavimentos e lógica semelhante ao unifamiliar
        # quando cabível). Para não criar contradição, a permeabilidade deve
        # acompanhar a área adotada nessa leitura, e não recalcular novamente
        # pelo cenário conservador dos recuos padrão.
        base_ocupacao = ctx.get("a_adotada") or ctx.get("teto_relatorio") or area_to
        try:
            base_ocupacao = float(base_ocupacao) if base_ocupacao is not None else None
        except Exception:
            base_ocupacao = None
        if base_ocupacao is None:
            st.info("Sem dados suficientes para montar a leitura de permeabilidade do R2.1.")
            return
        decision = None
    else:
        decision = choose_regular_occupancy(
            area_to=area_to,
            area_recuos=area_recuos,
            area_pretendida=area_pedida,
        )
        base_ocupacao = decision.area_adotada
        if base_ocupacao is None:
            st.info("Sem dados suficientes para montar os cenários de permeabilidade.")
            return

    area_restante = area_lote - base_ocupacao
    area_impermeavel_livre = area_restante - area_permeavel_min

    if ctx.get("is_r21"):
        md("**Permeabilidade no R2.1**")
        md(
            "A área permeável é a parte do terreno que precisa permitir a infiltração da água da chuva no solo. "
            "No R2.1, mesmo existindo duas unidades habitacionais, a regra de permeabilidade continua sendo calculada sobre a **área total do lote**, e não separadamente para cada unidade."
        )
        md("**Cálculo usando o limite adotado para o R2.1**")
        if area_pedida_valida and area_pedida <= base_ocupacao:
            md(f"Como o usuário informou **{fmt_num(area_pedida)} m²** no térreo e essa área está dentro do limite adotado, a análise da permeabilidade considera essa área.")
        else:
            md(f"Este item considera **{fmt_num(base_ocupacao)} m²** como ocupação de referência, acompanhando a leitura do R2.1 apresentada no item anterior.")
        if area_recuos is not None:
            md(
                f"Como conferência conservadora, os recuos padrão da zona indicam uma área física de **{fmt_num(area_recuos)} m²**. "
                "Esse número serve apenas para comparação com a leitura principal do R2.1 apresentada no item anterior. "
                "No R2.1, pode haver uma leitura mais flexível dos recuos de frente e laterais quando cabível, mas a ocupação adotada continua limitada pela TO, pela TP, pelo recuo de fundos, pelo limite de até 2 pavimentos e pela confirmação no licenciamento."
            )
    elif area_pedida_valida:
        if decision.area_pretendida_acima_to or decision.area_pretendida_acima_recuos:
            md("**Cenário 1 — usando o máximo da TO e o limite físico aplicável**")
            md("**Cálculo usando a área adotada no relatório**")
            if decision.area_pretendida_acima_to:
                md(f"A área pretendida de **{fmt_num(area_pedida)} m²** ultrapassa a TO máxima permitida.")
            if decision.area_pretendida_acima_recuos:
                md("**Cenário 2 — usando a implantação pelos recuos da zona**")
                md(f"A área pretendida de **{fmt_num(area_pedida)} m²** ultrapassa a área física estimada pelos recuos.")
            md(
                f"A leitura de ocupação adotou **{fmt_num(base_ocupacao)} m²** como referência, usando o menor limite aplicável entre TO, recuos e área pretendida."
            )
        else:
            md("**Cálculo usando a área digitada pelo usuário**")
            md(f"Como o usuário informou **{fmt_num(area_pedida)} m²** no térreo, a análise da permeabilidade passa a considerar esse valor.")
    else:
        md("**Cálculo usando o limite de ocupação adotado**")
        if decision.recuos_mais_restritivos:
            md(f"Como os recuos são mais restritivos que a TO, este item considera **{fmt_num(base_ocupacao)} m²** como ocupação de referência.")
        else:
            md(f"Este item considera **{fmt_num(base_ocupacao)} m²** como ocupação de referência no térreo.")

    if area_recuos is not None and not ctx.get("is_r21"):
        md(f"Pelos recuos, a construção até caberia fisicamente em uma área de **{fmt_num(area_recuos)} m²**. Porém, isso **não significa que seja permitido ocupar tudo isso**.")

    md(f"👉 **Área restante no lote: {fmt_num(area_lote)} − {fmt_num(base_ocupacao)} = {fmt_num(area_restante)}**")
    md("Desses:")
    md(f"- **{fmt_num(area_permeavel_min)}** devem permitir infiltração no solo")
    md(f"- **{fmt_num(max(area_impermeavel_livre, 0.0))}** podem receber piso impermeável")

    if area_impermeavel_livre < 0:
        deficit = abs(area_impermeavel_livre)
        md(
            f"👉 **Atenção:** com essa ocupação, a área livre não atende à permeabilidade mínima. Há déficit de **{fmt_num(deficit)} m²** de área permeável."
        )
    else:
        md(
            f"👉 **Leitura prática:** considerando **{fmt_num(base_ocupacao)} m²** no térreo, ainda sobram **{fmt_num(area_restante)} m²** livres. Desse total, **{fmt_num(area_permeavel_min)} m²** precisam permanecer permeáveis, e **{fmt_num(area_impermeavel_livre)} m²** podem receber piso impermeável."
        )

    md(
        "👉 **Regra de coerência:** o cálculo de permeabilidade usa a mesma área adotada no item de ocupação do térreo."
    )
