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



def _to_float(value):
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None


def _min_valid(*values):
    nums = [float(v) for v in values if _to_float(v) is not None]
    return min(nums) if nums else None


def _r21_metrics(area_lote, area_to, tp_m2, rec_fun, lot_front_original, lot_depth_original):
    front = _to_float(lot_front_original)
    depth = _to_float(lot_depth_original)
    fundo = _to_float(rec_fun) or 0.0
    area_fisica = None
    profundidade_util = None
    if front is not None and depth is not None and front > 0 and depth > fundo:
        profundidade_util = depth - fundo
        area_fisica = front * profundidade_util
    limite_permeabilidade = None
    lote = _to_float(area_lote)
    tp = _to_float(tp_m2)
    if lote is not None and tp is not None:
        limite_permeabilidade = max(lote - tp, 0.0)
    limite_real = _min_valid(area_to, area_fisica, limite_permeabilidade)
    return area_fisica, profundidade_util, limite_permeabilidade, limite_real

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
            tp_m2 = ctx.get("tp_m2")
            area_fisica_r21, profundidade_art112, limite_tp, limite_real = _r21_metrics(
                area_lote, area_to, tp_m2, rec_fun, lot_front_original, lot_depth_original
            )
            limite_real = limite_real if limite_real is not None else area_to
            area_por_unidade = (limite_real / 2.0) if limite_real is not None else None

            md(
                "**Texto didático para R2.1**\n\n"
                "O **R2.1 é um multifamiliar, mas tem uma regra especial**. Ele é formado por **2 unidades no mesmo lote**, lado a lado ou uma sobre a outra. "
                "Mesmo sendo classificado como multifamiliar, a **LC 90/2023** determina que cada unidade seja analisada, em alguns pontos, como uma **residência unifamiliar**.\n\n"
                "Isso significa que cada unidade precisa ter:\n\n"
                "- **frente e acesso independente para a via pública oficial**;\n"
                "- **paredes externas total ou parcialmente comuns**;\n"
                "- **aparência de um único conjunto arquitetônico**;\n"
                "- **no máximo 2 pavimentos**;\n"
                "- **ambientes mínimos conforme as regras da residência unifamiliar**.\n\n"
                "**Na prática:** para os recuos, o R2.1 pode seguir a lógica aplicada ao unifamiliar. Por isso, quando couber, pode ser considerada a flexibilidade do **art. 112**, que permite zerar recuos de frente e laterais, desde que o projeto continue respeitando a **Taxa de Ocupação (TO)** máxima e a **Taxa de Permeabilidade (TP)** mínima da zona."
            )
            md("**Como o sistema calcula neste caso**")
            md(
                "O sistema calcula em etapas: primeiro verifica os limites da zona, como **Taxa de Ocupação (TO)**, **Taxa de Permeabilidade (TP)**, **Índice de Aproveitamento (IA)**, altura e recuo de fundos. Depois, por ser R2.1, apresenta a leitura das duas formas possíveis: **unidades sobrepostas** e **unidades lado a lado**. Em qualquer cenário, vale sempre o limite mais restritivo."
            )
            md("**Conferência física com a lógica do unifamiliar / art. 112**")
            md(f"Largura considerada: **{fmt_num(lot_front_original)} m**")
            md(f"Profundidade considerada: **{fmt_num(lot_depth_original)} m**")
            md(f"Recuo de fundos: **{fmt_num(rec_fun)} m**")
            if area_fisica_r21 is not None:
                md(f"👉 Pelos recuos aplicáveis nessa leitura, a construção até caberia fisicamente em **{fmt_num(area_fisica_r21)} m²** (**{fmt_num(lot_front_original)} × {fmt_num(profundidade_art112)}**).")
            if limite_tp is not None:
                md(f"👉 Pela **Taxa de Permeabilidade (TP)**, o lote precisa manter **{fmt_num(tp_m2)} m²** permeáveis. Assim, a ocupação no térreo também não deve passar de **{fmt_num(limite_tp)} m²** para preservar essa área livre mínima.")
            md(f"👉 Pela **Taxa de Ocupação (TO)**, o limite do térreo é **{fmt_num(area_to)} m²**. Portanto, para este lote, o **limite real de ocupação no térreo** é **{fmt_num(limite_real)} m²**.")
            md("**Cenário A — unidades sobrepostas**")
            md("Nesse cenário, uma unidade fica no térreo e a outra no pavimento superior. A projeção no chão pode usar o limite real permitido para o térreo, respeitando a **Taxa de Ocupação (TO)**, a **Taxa de Permeabilidade (TP)**, os recuos aplicáveis e o limite de **2 pavimentos**.")
            md(f"👉 Projeção máxima de referência no térreo: **{fmt_num(limite_real)} m²**.")
            md("**Cenário B — unidades lado a lado**")
            md("Nesse cenário, as duas unidades ficam no térreo e dividem a área permitida. A área máxima do térreo **não dobra** por existir mais de uma unidade; ela precisa ser distribuída entre as duas casas, seus acessos e as áreas necessárias.")
            if area_por_unidade is not None:
                md(f"👉 Se a divisão fosse igual apenas como referência inicial, cada unidade teria aproximadamente **{fmt_num(area_por_unidade)} m²** de projeção no térreo. O projeto real pode distribuir de outra forma, desde que cada unidade tenha frente e acesso independente para a via pública oficial e cumpra os ambientes mínimos.")
            md("**Resumo final**")
            md(f"Em resumo: o R2.1 pode ser sobreposto ou lado a lado, mas a ocupação do térreo continua limitada pela **Taxa de Ocupação (TO)**, pela **Taxa de Permeabilidade (TP)** e pelo que cabe fisicamente no lote pelos recuos aplicáveis. Neste caso, o limite real do térreo é **{fmt_num(limite_real)} m²**.")
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
        tp_m2 = ctx.get("tp_m2")
        area_fisica_r21, profundidade_art112, limite_tp, limite_real = _r21_metrics(
            area_lote, area_to, tp_m2, rec_fun, lot_front_original, lot_depth_original
        )
        limite_real = limite_real if limite_real is not None else area_to
        area_por_unidade = (limite_real / 2.0) if limite_real is not None else None

        md(f"👉 **Área pretendida informada: {fmt_num(area_pedida)} m²**")
        if to_utilizada is not None:
            md("Para essa área pretendida, a **Taxa de Ocupação (TO)** utilizada no projeto fica assim:")
            md(f"👉 **{fmt_num(area_pedida)} ÷ {fmt_num(area_lote)} × 100 = {_fmt_pct_local(to_utilizada)}**")
            if area_pedida <= area_to:
                md(f"Isso significa que a proposta ocupa **{_fmt_pct_local(to_utilizada)}** do lote no térreo, ficando dentro do limite máximo da zona, que é de **{to_txt}**.")
            else:
                md(f"Isso significa que a proposta ocupa **{_fmt_pct_local(to_utilizada)}** do lote no térreo, ultrapassando o limite máximo da zona, que é de **{to_txt}**.")
        md("**Como o sistema calcula o R2.1:** primeiro são considerados os limites da zona — **Taxa de Ocupação (TO)**, **Taxa de Permeabilidade (TP)**, **Índice de Aproveitamento (IA)**, altura e recuo de fundos. Depois, por ser R2.1, o relatório mostra as duas formas possíveis de implantação: **unidades sobrepostas** e **unidades lado a lado**.")
        if area_fisica_r21 is not None:
            md(f"Pelos recuos aplicáveis à leitura do unifamiliar/art. 112, a construção até caberia fisicamente em **{fmt_num(area_fisica_r21)} m²**. Porém, isso não significa que seja permitido ocupar tudo isso.")
        md(f"Pela **Taxa de Ocupação (TO)**, o limite do térreo é **{fmt_num(area_to)} m²**.")
        if limite_tp is not None:
            md(f"Pela **Taxa de Permeabilidade (TP)**, também é necessário manter área livre permeável, deixando como referência máxima de ocupação **{fmt_num(limite_tp)} m²**.")
        md(f"Portanto, o **limite real de ocupação no térreo** para esta análise é **{fmt_num(limite_real)} m²**.")
        md("**Cenário A — unidades sobrepostas**")
        md(f"Uma unidade fica no térreo e a outra no pavimento superior. A projeção no chão pode usar até **{fmt_num(limite_real)} m²**, desde que sejam respeitados a **Taxa de Ocupação (TO)**, a **Taxa de Permeabilidade (TP)**, os recuos aplicáveis, o **Índice de Aproveitamento (IA)** e o limite de **2 pavimentos**.")
        md("**Cenário B — unidades lado a lado**")
        md("As duas unidades dividem a área permitida no térreo. A área máxima do térreo não dobra; ela precisa ser distribuída entre as duas casas, seus acessos e as áreas necessárias.")
        if area_por_unidade is not None:
            md(f"👉 Se a divisão fosse igual apenas como referência inicial, cada unidade teria aproximadamente **{fmt_num(area_por_unidade)} m²** de projeção no térreo.")
        if area_pedida <= limite_real:
            md(f"👉 Como a área pretendida informada foi de **{fmt_num(area_pedida)} m²**, ela fica dentro do limite real de **{fmt_num(limite_real)} m²**. A proposta ainda precisa ser desenvolvida respeitando os acessos independentes, os ambientes mínimos e a análise do licenciamento.")
        else:
            md(f"👉 Como a área pretendida informada foi de **{fmt_num(area_pedida)} m²**, ela ultrapassa o limite real de **{fmt_num(limite_real)} m²**. Para esta hipótese, o estudo deve adotar **{fmt_num(limite_real)} m²** como teto de referência no térreo.")
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
