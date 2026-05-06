from __future__ import annotations

import streamlit as st

from .common import md, fmt_num, fmt_pct


def _fmt_pct_local(v) -> str:
    try:
        return f"{float(v):.1f}%".replace(".", ",")
    except Exception:
        return "—"


def _is_r21(ctx: dict) -> bool:
    multi_tipo = str(ctx.get("multi_tipo") or "").upper()
    use_type_code = str(ctx.get("use_type_code") or "").upper()
    return ctx.get("is_r21") is True or multi_tipo in ("R21", "R2.1", "R2_1") or use_type_code.endswith("R21")


def _is_r22(ctx: dict) -> bool:
    multi_tipo = str(ctx.get("multi_tipo") or "").upper()
    use_type_code = str(ctx.get("use_type_code") or "").upper()
    return multi_tipo in ("R22", "R2.2", "R2_2") or use_type_code.endswith("R22")


def _is_r3(ctx: dict) -> bool:
    multi_tipo = str(ctx.get("multi_tipo") or "").upper()
    use_type_code = str(ctx.get("use_type_code") or "").upper()
    return multi_tipo in ("R3", "R03") or use_type_code.endswith("R3")


def render(ctx: dict) -> None:
    area_lote = ctx.get("lot_area_f")
    to_max = ctx.get("to_max_pct")
    area_to = ctx.get("to_m2")
    area_pedida = ctx.get("built_ground")
    a_recuos = ctx.get("A_recuos")
    rec_fr = ctx.get("rec_fr")
    rec_lat = ctx.get("rec_lat")
    rec_fun = ctx.get("rec_fun")
    w_util = ctx.get("W_util")
    d_util = ctx.get("D_util")
    lot_front = ctx.get("lot_front")
    lot_depth = ctx.get("lot_depth")

    def _dim_original(valor_original, valor_util, *recuos):
        """Mostra a dimensão original de forma robusta.

        Em alguns fluxos antigos o contexto pode trazer a profundidade útil no campo
        de profundidade. Quando isso acontece, recuperamos a dimensão original pela
        soma da dimensão útil com os recuos aplicados.
        """
        try:
            util = float(valor_util) if valor_util not in (None, "") else None
            soma_recuos = sum(float(r or 0) for r in recuos)
            if util is not None and util > 0:
                estimada = util + soma_recuos
                original = float(valor_original) if valor_original not in (None, "") else None
                if original is None or abs(original - util) < 0.01:
                    return estimada
                if original + 0.01 < estimada:
                    return estimada
                return original
        except Exception:
            pass
        return valor_original

    lot_front_original = _dim_original(lot_front, w_util, rec_lat, rec_lat)
    lot_depth_original = _dim_original(lot_depth, d_util, rec_fr, rec_fun)

    if area_lote is None or to_max is None or area_to is None:
        st.info("Sem TO máxima cadastrada para esta zona/uso.")
        return

    to_txt = _fmt_pct_local(to_max)
    r21 = _is_r21(ctx)
    r22 = _is_r22(ctx)
    r3 = _is_r3(ctx)

    md(
        f"A zona permite ocupar até **{to_txt}** do terreno no térreo.\n\n"
        f"👉 **{fmt_num(area_lote)} × {to_txt} = {fmt_num(area_to)}**\n\n"
        "Esse é o limite máximo permitido pela Taxa de Ocupação (TO)."
    )

    # Sem área pretendida
    if area_pedida in (None, "", 0):
        if r21:
            md(
                f"Na prática, isso significa que a edificação não pode ultrapassar **{fmt_num(area_to)}** no térreo, considerando a ocupação máxima permitida pela zona."
            )

            md("**Opção 1 — usando os recuos da zona**")
            md("No caso de usar todos os recuos conforme a zona, a área útil de implantação fica assim:")
            md("**1. Cálculo da largura útil**")
            md(f"A largura original do lote é de **{fmt_num(lot_front_original)} m**.")
            md("Como a zona exige:")
            md(f"**{fmt_num(rec_lat)}** de recuo lateral de um lado")
            md(f"**{fmt_num(rec_lat)}** de recuo lateral do outro lado")
            md("fazemos:")
            md(f"👉 **{fmt_num(lot_front_original)} − {fmt_num(rec_lat)} − {fmt_num(rec_lat)} = {fmt_num(w_util)}**")
            md(f"Largura útil: **{fmt_num(w_util)}**")

            md("**2. Cálculo da profundidade útil**")
            md(f"A profundidade original do lote é de **{fmt_num(lot_depth_original)} m**.")
            md("Como a zona exige:")
            md(f"**{fmt_num(rec_fr)}** de recuo frontal")
            md(f"**{fmt_num(rec_fun)}** de recuo de fundo")
            md("fazemos:")
            md(f"👉 **{fmt_num(lot_depth_original)} − {fmt_num(rec_fr)} − {fmt_num(rec_fun)} = {fmt_num(d_util)}**")
            md(f"Profundidade útil: **{fmt_num(d_util)}**")

            md("**3. Cálculo da área útil de implantação**")
            md(f"👉 **{fmt_num(w_util)} × {fmt_num(d_util)} = {fmt_num(a_recuos)}**")
            md(
                f"Leitura prática: pelos recuos, a construção até caberia fisicamente em uma área de **{fmt_num(a_recuos)} m²**. "
                f"Porém, isso não significa que seja permitido ocupar tudo isso: a Taxa de Ocupação limita o térreo a **{fmt_num(area_to)} m²**."
            )

            md("**Opção 2 — no caso do multifamiliar justaposto**")
            md(
                "Informação importante: quando a zona permitir usar parâmetros semelhantes aos do unifamiliar, o projeto pode encostar nas laterais e zerar o recuo frontal."
            )
            md(
                f"👉 Nesse cenário, o aproveitamento do térreo pode chegar ao limite da TO máxima da zona, que neste caso é de **{fmt_num(area_to)}**, desde que sejam respeitadas a adequabilidade, a Taxa de Ocupação (TO) e a Taxa de Permeabilidade (TP)."
            )

            md("**Resumo final**")
            md(
                f"Neste caso, a zona permite ocupar até **{fmt_num(area_to)} m²** no térreo pela Taxa de Ocupação (TO).\n"
                f"Se forem aplicados os recuos da zona, a área útil de implantação fica em **{fmt_num(a_recuos)} m²**.\n"
                f"Já no caso do multifamiliar justaposto, quando a zona permitir leitura semelhante ao unifamiliar, o aproveitamento do térreo pode chegar a **{fmt_num(area_to)} m²**, desde que sejam respeitadas as demais exigências urbanísticas aplicáveis."
            )
            return

        # R2.2 e R3 sem área pretendida
        md(
            "Mas o que isso significa na prática? A TO mostra o limite percentual permitido pela zona. Só que, no projeto real, a implantação também precisa respeitar os recuos obrigatórios da zona."
        )
        md("**Recuos da zona**")
        md(f"Frontal: **{fmt_num(rec_fr)}**")
        md(f"Laterais: **{fmt_num(rec_lat)}**")
        md(f"Fundo: **{fmt_num(rec_fun)}**")

        md("**Cálculo da largura útil**")
        md(f"A largura original do lote é de **{fmt_num(lot_front_original)} m**.")
        md(f"👉 **{fmt_num(lot_front_original)} − recuos laterais = {fmt_num(w_util)}**")
        md(f"Largura útil: **{fmt_num(w_util)}**")

        md("**Cálculo da profundidade útil**")
        md(f"A profundidade original do lote é de **{fmt_num(lot_depth_original)} m**.")
        md(f"👉 **{fmt_num(lot_depth_original)} − recuo frontal − recuo de fundo = {fmt_num(d_util)}**")
        md(f"Profundidade útil: **{fmt_num(d_util)}**")

        md("**Cálculo da área útil de implantação**")
        md(f"👉 **{fmt_num(w_util)} × {fmt_num(d_util)} = {fmt_num(a_recuos)}**")

        md("**Leitura prática**")
        md(f"👉 Pela Taxa de Ocupação, o lote poderia ocupar até **{fmt_num(area_to)}** no térreo.")
        md(f"👉 Pelos recuos, a construção até caberia fisicamente em uma área de **{fmt_num(a_recuos)} m²**.")
        md("Porém, isso **não significa que seja permitido ocupar tudo isso**.")
        md(f"Neste caso, a Taxa de Ocupação é mais restritiva e limita a ocupação do térreo a **{fmt_num(area_to)} m²**.")
        md(f"Portanto, para este lote, o limite real de ocupação no térreo é **{fmt_num(area_to)} m²**.")
        return

    # Com área pretendida
    try:
        to_utilizada = (float(area_pedida) / float(area_lote)) * 100.0
    except Exception:
        to_utilizada = None

    if r21:
        md(f"👉 **Área pretendida informada: {fmt_num(area_pedida)} m²**")
        if to_utilizada is not None:
            md("Para essa área pretendida, a Taxa de Ocupação utilizada no projeto fica assim:")
            md(f"👉 **{fmt_num(area_pedida)} ÷ {fmt_num(area_lote)} × 100 = {_fmt_pct_local(to_utilizada)}**")
            if area_pedida <= area_to:
                md(
                    f"Isso significa que a proposta ocupa **{_fmt_pct_local(to_utilizada)}** do lote no térreo, ficando dentro do limite máximo da zona, que é de **{to_txt}**."
                )
            else:
                md(
                    f"Isso significa que a proposta ocupa **{_fmt_pct_local(to_utilizada)}** do lote no térreo, ultrapassando o limite máximo da zona, que é de **{to_txt}**."
                )

        md("**Opção 1 — usando os recuos da zona**")
        md("No caso de usar todos os recuos conforme a zona, a área útil de implantação fica assim:")
        md("**1. Cálculo da largura útil**")
        md(f"A largura original do lote é de **{fmt_num(lot_front_original)} m**.")
        md("Como a zona exige:")
        md(f"**{fmt_num(rec_lat)} m** de recuo lateral de um lado")
        md(f"**{fmt_num(rec_lat)} m** de recuo lateral do outro lado")
        md("fazemos:")
        md(f"👉 **{fmt_num(lot_front_original)} − {fmt_num(rec_lat)} − {fmt_num(rec_lat)} = {fmt_num(w_util)}**")
        md(f"Largura útil: **{fmt_num(w_util)} m**")

        md("**2. Cálculo da profundidade útil**")
        md(f"A profundidade original do lote é de **{fmt_num(lot_depth_original)} m**.")
        md("Como a zona exige:")
        md(f"**{fmt_num(rec_fr)} m** de recuo frontal")
        md(f"**{fmt_num(rec_fun)} m** de recuo de fundo")
        md("fazemos:")
        md(f"👉 **{fmt_num(lot_depth_original)} − {fmt_num(rec_fr)} − {fmt_num(rec_fun)} = {fmt_num(d_util)}**")
        md(f"Profundidade útil: **{fmt_num(d_util)} m**")

        md("**3. Cálculo da área útil de implantação**")
        md(f"👉 **{fmt_num(w_util)} × {fmt_num(d_util)} = {fmt_num(a_recuos)} m²**")

        if area_pedida <= a_recuos:
            md(
                f"👉 Comparando com a área pretendida: como o usuário informou **{fmt_num(area_pedida)} m²**, esse valor cabe dentro da área útil de implantação com recuos, que neste caso é de **{fmt_num(a_recuos)} m²**."
            )
            md(
                f"Leitura prática: isso significa que, além de respeitar a TO máxima da zona, a implantação pretendida de **{fmt_num(area_pedida)} m²** também cabe fisicamente no lote quando se aplicam todos os recuos obrigatórios."
            )
        else:
            md(
                f"👉 Comparando com a área pretendida: como o usuário informou **{fmt_num(area_pedida)} m²**, esse valor ultrapassa a área útil de implantação com recuos, que neste caso é de **{fmt_num(a_recuos)} m²**."
            )
            md(
                f"Leitura prática: isso significa que, além de ultrapassar a TO máxima da zona, a implantação pretendida de **{fmt_num(area_pedida)} m²** também não cabe fisicamente no lote quando se aplicam todos os recuos obrigatórios."
            )

        md("**Opção 2 — no caso do multifamiliar justaposto**")
        md(
            "Informação importante: quando a zona permitir usar parâmetros semelhantes aos do unifamiliar, o projeto pode encostar nas laterais e zerar o recuo frontal."
        )
        md(
            f"👉 Nesse cenário, o aproveitamento do térreo pode chegar ao limite da TO máxima da zona, que neste caso é de **{fmt_num(area_to)} m²**, desde que sejam respeitadas a adequabilidade, a Taxa de Ocupação (TO) e a Taxa de Permeabilidade (TP)."
        )

        if area_pedida <= area_to:
            md(
                f"👉 Comparando com a área pretendida: como o usuário informou **{fmt_num(area_pedida)} m²**, essa proposta corresponde a uma ocupação de **{_fmt_pct_local(to_utilizada)}** do lote e também fica dentro dessa leitura, pois permanece abaixo do limite máximo de **{to_txt}** de TO."
            )
            md("**Resumo final**")
            md(
                f"Neste caso, a zona permite ocupar até **{to_txt}** do lote no térreo, o que corresponde a **{fmt_num(area_to)} m²**.\n\n"
                f"Como o usuário informou uma área pretendida de **{fmt_num(area_pedida)} m²**, a ocupação proposta representa **{_fmt_pct_local(to_utilizada)}** do terreno, ficando dentro da TO máxima permitida pela zona.\n\n"
                f"Se forem aplicados os recuos da zona, a área útil de implantação fica em **{fmt_num(a_recuos)} m²**, e a área pretendida de **{fmt_num(area_pedida)} m²** também cabe dentro desse limite físico.\n\n"
                f"Já no caso do multifamiliar justaposto, quando a zona permitir leitura semelhante ao unifamiliar, a proposta também permanece compatível, pois continua abaixo do limite máximo permitido pela TO.\n\n"
                f"👉 Em resumo, a área pretendida de **{fmt_num(area_pedida)} m²** é viável tanto do ponto de vista percentual da Taxa de Ocupação quanto da implantação prática no lote."
            )
        else:
            md(
                f"👉 Comparando com a área pretendida: como o usuário informou **{fmt_num(area_pedida)} m²**, essa proposta corresponde a uma ocupação de **{_fmt_pct_local(to_utilizada)}** do lote e não fica dentro dessa leitura, pois ultrapassa o limite máximo de **{to_txt}** de TO."
            )
            md("**Resumo final**")
            md(
                f"Neste caso, a zona permite ocupar até **{to_txt}** do lote no térreo, o que corresponde a **{fmt_num(area_to)} m²**.\n\n"
                f"Como o usuário informou uma área pretendida de **{fmt_num(area_pedida)} m²**, a ocupação proposta representa **{_fmt_pct_local(to_utilizada)}** do terreno, ultrapassando a TO máxima permitida pela zona.\n\n"
                f"Se forem aplicados os recuos da zona, a área útil de implantação fica em **{fmt_num(a_recuos)} m²**, e a área pretendida de **{fmt_num(area_pedida)} m²** também não cabe dentro desse limite físico.\n\n"
                f"Já no caso do multifamiliar justaposto, quando a zona permitir leitura semelhante ao unifamiliar, a proposta continua incompatível, pois permanece acima do limite máximo permitido pela TO.\n\n"
                f"👉 Em resumo, a área pretendida de **{fmt_num(area_pedida)} m²** não é viável nem do ponto de vista percentual da Taxa de Ocupação nem da implantação prática no lote."
            )
        return

    # R2.2 e R3 com área pretendida
    md(f"👉 **Área pretendida informada pelo usuário: {fmt_num(area_pedida)} m²**")
    md("Para essa proposta, a taxa de ocupação utilizada fica assim:")
    md(f"👉 **{fmt_num(area_pedida)} ÷ {fmt_num(area_lote)} × 100 = {_fmt_pct_local(to_utilizada)}**")

    if area_pedida <= area_to:
        md(
            f"Isso significa que a proposta ocupa **{_fmt_pct_local(to_utilizada)}** do lote no térreo, ficando dentro do limite máximo da zona, que é de **{to_txt}**."
        )
    else:
        md(
            f"Isso significa que a proposta ocuparia **{_fmt_pct_local(to_utilizada)}** do lote no térreo, ultrapassando o limite máximo da zona, que é de **{to_txt}**."
        )
        md(
            f"👉 **Como a área informada pelo usuário é inviável para este lote, por ultrapassar a TO máxima permitida, a análise passa a continuar considerando o limite máximo permitido pela zona, que é de {fmt_num(area_to)} m².**"
        )

    md(
        "Mas o que isso significa na prática? A TO mostra o limite percentual permitido pela zona. Só que, no projeto real, a implantação também precisa respeitar os recuos obrigatórios da zona."
    )

    md("**Recuos da zona**")
    md(f"Frontal: **{fmt_num(rec_fr)}**")
    md(f"Laterais: **{fmt_num(rec_lat)}**")
    md(f"Fundo: **{fmt_num(rec_fun)}**")

    md("**Cálculo da largura útil**")
    md(f"A largura original do lote é de **{fmt_num(lot_front_original)} m**.")
    md(f"👉 **{fmt_num(lot_front_original)} − recuos laterais = {fmt_num(w_util)}**")
    md(f"Largura útil: **{fmt_num(w_util)}**")

    md("**Cálculo da profundidade útil**")
    md(f"A profundidade original do lote é de **{fmt_num(lot_depth_original)} m**.")
    md(f"👉 **{fmt_num(lot_depth_original)} − recuo frontal − recuo de fundo = {fmt_num(d_util)}**")
    md(f"Profundidade útil: **{fmt_num(d_util)}**")

    md("**Cálculo da área útil de implantação**")
    md(f"👉 **{fmt_num(w_util)} × {fmt_num(d_util)} = {fmt_num(a_recuos)}**")

    md("**Leitura prática**")
    if area_pedida <= area_to:
        md(
            f"👉 Pela Taxa de Ocupação, a proposta informada pelo usuário utiliza **{_fmt_pct_local(to_utilizada)}** do lote, equivalente a **{fmt_num(area_pedida)} m²** no térreo, ficando dentro do limite máximo permitido pela zona."
        )
        md(
            f"👉 Pelos recuos, a construção até caberia fisicamente em uma área de **{fmt_num(a_recuos)} m²**."
        )
        md(
            f"👉 Como a área pretendida informada foi de **{fmt_num(area_pedida)} m²**, ela cabe dentro desse espaço físico e também fica abaixo da TO."
        )
        md("Ou seja:")
        md("- a TO mostra que a proposta está dentro do limite urbanístico da zona;")
        md("- os recuos mostram que a área pretendida também cabe fisicamente no lote.")
        md(
            f"👉 Neste caso, os **{fmt_num(area_pedida)} m²** informados são viáveis pela Taxa de Ocupação e pelos recuos."
        )
    else:
        md(
            f"👉 Pela Taxa de Ocupação, o lote poderia ocupar até **{fmt_num(area_to)} m²** no térreo, mas a área digitada pelo usuário foi de **{fmt_num(area_pedida)} m²**, o que não é permitido, porque ultrapassa a TO máxima da zona."
        )
        md(
            f"👉 Por isso, para continuidade do estudo, a análise passa a considerar **{fmt_num(area_to)} m²** como limite urbanístico máximo pela TO."
        )
        md(
            f"👉 Pelos recuos, a construção até caberia fisicamente em uma área de **{fmt_num(a_recuos)} m²**."
        )
        md("Porém, isso **não significa que seja permitido ocupar tudo isso**.")
        md("Ou seja:")
        md(f"- a TO mostra que os **{fmt_num(area_pedida)} m²** informados são inviáveis, pois excedem o limite máximo da zona;")
        md(f"- os recuos mostram apenas o espaço físico disponível, mas o limite real continua sendo **{fmt_num(area_to)} m²** pela TO.")
        md(
            f"👉 Neste caso, os **{fmt_num(area_pedida)} m²** informados não podem ser adotados. Como essa área ultrapassa a TO máxima permitida, o estudo continua com o máximo permitido pela zona, que é de **{fmt_num(area_to)} m²**."
        )
