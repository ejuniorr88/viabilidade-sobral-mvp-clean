from __future__ import annotations

import streamlit as st

from .common import md, fmt_num


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

    # Regra pedida pelo usuário:
    # - vazio, 0, inválido ou acima da TO => mantém o comportamento atual
    # - maior que 0 e dentro da TO => calcula em cima do valor digitado
    if area_pedida_dentro_to:
        area_restante = area_lote - area_pedida
        area_impermeavel_livre = area_restante - area_permeavel_min

        md("**Cálculo usando a área digitada pelo usuário**")
        md(f"Como o usuário informou **{fmt_num(area_pedida)} m²** no térreo, a análise da permeabilidade passa a considerar esse valor.")

        md(f"👉 **Área restante no lote: {fmt_num(area_lote)} − {fmt_num(area_pedida)} = {fmt_num(area_restante)}**")

        if area_impermeavel_livre >= 0:
            md("Desses:")
            md(f"- **{fmt_num(area_permeavel_min)}** devem permitir infiltração no solo")
            md(f"- **{fmt_num(area_impermeavel_livre)}** podem receber piso impermeável")

            md(
                f"👉 **Leitura prática:** com a implantação proposta de **{fmt_num(area_pedida)} m²**, ainda sobram "
                f"**{fmt_num(area_restante)} m²** livres no lote. Desse total, **{fmt_num(area_permeavel_min)} m²** "
                f"precisam permanecer permeáveis, e **{fmt_num(area_impermeavel_livre)} m²** ainda podem receber acabamento impermeável."
            )
        else:
            deficit = abs(area_impermeavel_livre)
            md("Desses:")
            md(f"- **{fmt_num(area_permeavel_min)}** deveriam permitir infiltração no solo")
            md(f"- **0,00** podem receber piso impermeável")

            md(
                f"👉 **Leitura prática:** embora a área digitada de **{fmt_num(area_pedida)} m²** esteja dentro da TO máxima, "
                f"ela **não atende à permeabilidade mínima**. Após essa implantação, restariam apenas **{fmt_num(area_restante)} m²** livres, "
                f"mas a zona exige **{fmt_num(area_permeavel_min)} m²** permeáveis. Isso gera um déficit de **{fmt_num(deficit)} m²**."
            )
        return

    # Comportamento atual preservado
    if area_to is None or area_recuos is None:
        st.info("Sem dados suficientes para montar os cenários de permeabilidade.")
        return

    area_restante_to = area_lote - area_to
    area_impermeavel_to = area_restante_to - area_permeavel_min

    # O cálculo pelos recuos mostra apenas a área que caberia fisicamente no lote.
    # Ele não pode virar cenário de ocupação quando for maior que a TO ou quando não deixar
    # área livre suficiente para a TP. Para relatório leigo, repetimos o limite real do térreo.
    limite_real_terreo = area_to
    area_restante_real = area_lote - limite_real_terreo
    area_impermeavel_real = area_restante_real - area_permeavel_min

    if area_pedida_valida and not area_pedida_dentro_to:
        md(
            f"👉 **Como a área digitada pelo usuário ({fmt_num(area_pedida)} m²) ultrapassa a TO máxima permitida, "
            f"este item continua considerando o limite real permitido no térreo, que é {fmt_num(limite_real_terreo)} m².**"
        )

    md("**Cenário 1 — usando o máximo da TO**")
    md(f"Se você utilizar **{fmt_num(limite_real_terreo)}** no térreo:")
    md(f"👉 **Área restante no lote: {fmt_num(area_lote)} − {fmt_num(limite_real_terreo)} = {fmt_num(area_restante_real)}**")
    md("Desses:")
    md(f"- **{fmt_num(area_permeavel_min)}** devem permitir infiltração no solo")
    md(f"- **{fmt_num(max(area_impermeavel_real, 0.0))}** podem receber piso impermeável")

    md("**Cenário 2 — usando a implantação pelos recuos da zona**")
    md(
        f"Pelos recuos, a construção até caberia fisicamente em uma área de **{fmt_num(area_recuos)} m²**. "
        "Porém, isso **não significa que seja permitido ocupar tudo isso**."
    )
    md(
        f"Neste caso, a Taxa de Ocupação é mais restritiva e limita a ocupação do térreo a **{fmt_num(limite_real_terreo)} m²**."
    )
    md(f"Portanto, para este lote, o limite real de ocupação no térreo é **{fmt_num(limite_real_terreo)} m²**.")
    md(f"Com esse limite, a área restante no lote continua sendo **{fmt_num(area_restante_real)} m²**.")
    md("Desses:")
    md(f"- **{fmt_num(area_permeavel_min)}** devem permitir infiltração no solo")
    md(f"- **{fmt_num(max(area_impermeavel_real, 0.0))}** podem receber piso impermeável")

    md(
        "👉 **Leitura prática:** no multifamiliar, a área física disponível pelos recuos ajuda a entender o desenho possível da implantação, "
        "mas o projeto não pode ultrapassar a TO nem deixar de atender à TP mínima."
    )
