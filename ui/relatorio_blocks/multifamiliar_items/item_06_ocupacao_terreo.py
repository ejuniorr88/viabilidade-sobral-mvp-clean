from __future__ import annotations

import streamlit as st

from .common import md, fmt_num, fmt_pct
from ui.relatorio_blocks.terreno_irregular import aviso_texto, limite_to_text
from urban_rules.common import choose_regular_occupancy


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

    if ctx.get("is_irregular"):
        md("**Terreno irregular — leitura pela área total**")
        md(aviso_texto())
        if r21:
            md(
                "**Observação para R2.1:** a tipologia continua limitada a **2 unidades** e **no máximo 2 pavimentos**. "
                "A distribuição das unidades, os acessos independentes e os recuos aplicáveis precisam ser definidos em planta, conforme a geometria real do lote."
            )
        if r3:
            md(
                "**Observação para R3:** por ser multifamiliar vertical, a implantação depende também de vagas, circulação, acessibilidade, área recreativa, afastamentos, iluminação/ventilação e demais exigências do licenciamento."
            )
        md(limite_to_text(fmt_num(area_to)))
        if area_pedida not in (None, "", 0):
            area_pedida_f = _to_float(area_pedida)
            if area_pedida_f is not None and area_pedida_f > float(area_to):
                md(f"👉 **A área pretendida de {fmt_num(area_pedida_f)} m² ultrapassa a Taxa de Ocupação máxima; o estudo deve considerar no máximo {fmt_num(area_to)} m² como limite pela TO.**")
            elif area_pedida_f is not None:
                md(f"👉 **A área pretendida de {fmt_num(area_pedida_f)} m² está dentro do limite máximo pela Taxa de Ocupação.**")
        else:
            md("👉 **Sem área pretendida informada, o relatório apresenta o limite máximo pela Taxa de Ocupação como referência inicial, sem cravar a implantação física do edifício.**")
        return

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
                "**Como o R2.1 é analisado neste lote**\n\n"
                "O **R2.1** corresponde à residência multifamiliar horizontal formada por **2 unidades habitacionais no mesmo lote**. "
                "Essas unidades podem ser implantadas de forma **sobreposta**, quando uma unidade fica acima da outra, ou de forma **justaposta**, quando ficam lado a lado.\n\n"
                "Mesmo sendo classificado como multifamiliar, o R2.1 possui regras próprias. Cada unidade deve ter **acesso independente para a via pública oficial**, e o conjunto deve manter **unidade arquitetônica**. Além disso, a tipologia fica limitada a **até 2 pavimentos**.\n\n"
                "Na prática, o sistema calcula primeiro os limites da zona, como **Taxa de Ocupação (TO)**, **Taxa de Permeabilidade (TP)**, **Índice de Aproveitamento (IA)**, altura e recuos. Depois, mostra como esses limites se aplicam às formas mais comuns de implantação do R2.1."
            )
            md(
                "Em alguns casos, a legislação permite uma leitura mais flexível dos recuos para esse tipo de moradia, desde que o projeto respeite a **ocupação máxima do terreno** e mantenha a **área permeável mínima**. Isso não significa aprovação automática: a implantação final ainda precisa ser conferida no licenciamento."
            )
            md("**Conferência inicial da implantação**")
            md(f"Largura considerada: **{fmt_num(lot_front_original)} m**")
            md(f"Profundidade considerada: **{fmt_num(lot_depth_original)} m**")
            md(f"Recuo de fundos: **{fmt_num(rec_fun)} m**")
            if area_fisica_r21 is not None:
                md(f"👉 Pelos recuos, a construção até caberia fisicamente em uma área de **{fmt_num(area_fisica_r21)} m²** (**{fmt_num(lot_front_original)} × {fmt_num(profundidade_art112)}**).")
            if limite_tp is not None:
                md(f"👉 Pela **Taxa de Permeabilidade (TP)**, o lote precisa manter **{fmt_num(tp_m2)} m²** permeáveis. Assim, a ocupação no térreo também não deve passar de **{fmt_num(limite_tp)} m²** para preservar essa área livre mínima.")
            md(f"👉 Pela **Taxa de Ocupação (TO)**, o limite do térreo é **{fmt_num(area_to)} m²**. Portanto, para este lote, o **limite real de ocupação no térreo** é **{fmt_num(limite_real)} m²**.")
            md("**Cenário A — unidades sobrepostas**")
            md("Nesse cenário, uma unidade fica no térreo e a outra no pavimento superior. A área ocupada no térreo corresponde à projeção da edificação sobre o lote. Por isso, ela deve respeitar a **Taxa de Ocupação (TO)**, a **Taxa de Permeabilidade (TP)**, os recuos aplicáveis e o limite de **até 2 pavimentos**.")
            md(f"👉 Projeção máxima de referência no térreo: **{fmt_num(limite_real)} m²**.")
            md("**Cenário B — unidades lado a lado**")
            md("Nesse cenário, as duas unidades ficam no térreo e dividem a área permitida. A área máxima do térreo **não dobra** por existir mais de uma unidade; ela precisa ser distribuída entre as duas casas, seus acessos e as áreas necessárias.")
            if area_por_unidade is not None:
                md(f"👉 Se a divisão fosse igual apenas como referência inicial, cada unidade teria aproximadamente **{fmt_num(area_por_unidade)} m²** de projeção no térreo. O projeto real pode distribuir de outra forma, desde que cada unidade tenha frente e acesso independente para a via pública oficial e cumpra os ambientes mínimos.")
            md("**Resumo final**")
            md(f"Em resumo: o R2.1 pode ser implantado com unidades sobrepostas ou justapostas. Em qualquer caso, a ocupação do térreo continua limitada pela **Taxa de Ocupação (TO)**, pela **Taxa de Permeabilidade (TP)**, pelos recuos aplicáveis e pelo limite de **até 2 pavimentos**. Para este lote, a referência de ocupação no térreo é de **{fmt_num(limite_real)} m²**.")
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
        decision = choose_regular_occupancy(area_to=area_to, area_recuos=a_recuos)
        limite_real = decision.area_adotada if decision.area_adotada is not None else area_to
        md(f"👉 Pela Taxa de Ocupação, o lote poderia ocupar até **{fmt_num(area_to)} m²** no térreo.")
        md(f"👉 Pelos recuos, a construção até caberia fisicamente em uma área de **{fmt_num(a_recuos)} m²**.")
        md("Porém, isso **não significa que seja permitido ocupar tudo isso**.")
        if decision.recuos_mais_restritivos:
            md(f"Neste caso, os recuos são mais restritivos que a TO, porque **{fmt_num(a_recuos)} m²** é menor que **{fmt_num(area_to)} m²**.")
        elif decision.to_mais_restritiva:
            md(f"Neste caso, a Taxa de Ocupação é mais restritiva e limita a ocupação do térreo a **{fmt_num(area_to)} m²**.")
        md(f"Portanto, para este lote, o limite real de ocupação no térreo é **{fmt_num(limite_real)} m²**.")
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
        md(
            "**Como o R2.1 é analisado neste lote**\n\n"
            "O **R2.1** corresponde à residência multifamiliar horizontal formada por **2 unidades habitacionais no mesmo lote**. "
            "Essas unidades podem ser implantadas de forma **sobreposta**, quando uma unidade fica acima da outra, ou de forma **justaposta**, quando ficam lado a lado.\n\n"
            "O sistema considera os limites da zona — **Taxa de Ocupação (TO)**, **Taxa de Permeabilidade (TP)**, **Índice de Aproveitamento (IA)**, altura e recuos — e mostra como esses limites se aplicam às duas formas de implantação."
        )
        if area_fisica_r21 is not None:
            md(f"Pelos recuos, a construção até caberia fisicamente em uma área de **{fmt_num(area_fisica_r21)} m²**. Porém, isso não significa que seja permitido ocupar tudo isso.")
        md(f"Pela **Taxa de Ocupação (TO)**, o limite do térreo é **{fmt_num(area_to)} m²**.")
        if limite_tp is not None:
            md(f"Pela **Taxa de Permeabilidade (TP)**, também é necessário manter área livre permeável, deixando como referência máxima de ocupação **{fmt_num(limite_tp)} m²**.")
        md(f"Portanto, o **limite real de ocupação no térreo** para esta análise é **{fmt_num(limite_real)} m²**.")
        md("**Cenário A — unidades sobrepostas**")
        md(f"Uma unidade fica no térreo e a outra no pavimento superior. A área ocupada no térreo corresponde à projeção da edificação sobre o lote. Para esta leitura, a referência de ocupação no térreo é de até **{fmt_num(limite_real)} m²**, respeitando a **Taxa de Ocupação (TO)**, a **Taxa de Permeabilidade (TP)**, os recuos aplicáveis, o **Índice de Aproveitamento (IA)** e o limite de **até 2 pavimentos**.")
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
    decision = choose_regular_occupancy(area_to=area_to, area_recuos=a_recuos, area_pretendida=area_pedida)
    area_adotada = decision.area_adotada if decision.area_adotada is not None else area_to
    md(f"👉 Pela Taxa de Ocupação, o lote poderia ocupar até **{fmt_num(area_to)} m²** no térreo.")
    md(f"👉 Pelos recuos, a construção até caberia fisicamente em uma área de **{fmt_num(a_recuos)} m²**.")

    if not decision.area_pretendida_acima_to and not decision.area_pretendida_acima_recuos:
        md(
            f"👉 Como a área pretendida informada foi de **{fmt_num(area_pedida)} m²**, ela fica dentro da TO e também cabe no envelope físico estimado pelos recuos."
        )
        md(f"👉 Neste caso, os **{fmt_num(area_pedida)} m²** informados podem ser adotados como referência inicial do térreo.")
    else:
        if decision.area_pretendida_acima_to:
            md(
                f"👉 A área digitada pelo usuário foi de **{fmt_num(area_pedida)} m²**, acima do limite máximo da TO de **{fmt_num(area_to)} m²**."
            )
        if decision.area_pretendida_acima_recuos:
            md(
                f"👉 A área digitada também ultrapassa a área física estimada pelos recuos, que é de **{fmt_num(a_recuos)} m²**."
            )
        md(
            f"👉 Para esta análise preliminar, o relatório deve adotar **{fmt_num(area_adotada)} m²** como limite de referência no térreo, usando o menor limite aplicável entre área pretendida, TO e recuos."
        )
