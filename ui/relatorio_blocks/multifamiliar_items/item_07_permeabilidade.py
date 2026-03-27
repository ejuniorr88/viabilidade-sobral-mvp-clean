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

    area_restante_recuos = area_lote - area_recuos
    area_impermeavel_recuos = area_restante_recuos - area_permeavel_min

    if area_pedida_valida and not area_pedida_dentro_to:
        md(
            f"👉 **Como a área digitada pelo usuário ({fmt_num(area_pedida)} m²) ultrapassa a TO máxima permitida, "
            f"este item continua com a lógica atual e analisa a permeabilidade a partir dos cenários padrão do sistema.**"
        )

    md("**Cenário 1 — usando o máximo da TO**")
    md(f"Se você utilizar **{fmt_num(area_to)}** no térreo:")
    md(f"👉 **Área restante no lote: {fmt_num(area_lote)} − {fmt_num(area_to)} = {fmt_num(area_restante_to)}**")
    md("Desses:")
    md(f"- **{fmt_num(area_permeavel_min)}** devem permitir infiltração no solo")
    md(f"- **{fmt_num(max(area_impermeavel_to, 0.0))}** podem receber piso impermeável")

    md("**Cenário 2 — usando a implantação pelos recuos da zona**")
    md(f"Se você utilizar **{fmt_num(area_recuos)}** no térreo:")
    md(f"👉 **Área restante no lote: {fmt_num(area_lote)} − {fmt_num(area_recuos)} = {fmt_num(area_restante_recuos)}**")
    md("Desses:")
    md(f"- **{fmt_num(area_permeavel_min)}** devem permitir infiltração no solo")
    md(f"- **{fmt_num(max(area_impermeavel_recuos, 0.0))}** podem receber piso impermeável")

    md(
        "👉 **Leitura prática:** no multifamiliar, quando a implantação aumenta, a área livre diminui. "
        "Por isso, quanto maior a ocupação do térreo, menor fica a sobra disponível além do mínimo exigido para a permeabilidade."
    )
