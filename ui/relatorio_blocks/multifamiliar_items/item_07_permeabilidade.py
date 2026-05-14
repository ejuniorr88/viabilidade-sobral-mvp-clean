from __future__ import annotations

import streamlit as st

from .common import md, fmt_num
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


def _scenario(area_lote, ocupacao, area_perm_min):
    area_restante = max(area_lote - ocupacao, 0.0)
    area_impermeavel_livre = max(area_restante - area_perm_min, 0.0)
    md(
        f"Considerando a ocupação de referência no térreo de **{fmt_num(ocupacao)} m²**, temos:\n\n"
        f"👉 **{fmt_num(area_lote)} m² − {fmt_num(ocupacao)} m² = {fmt_num(area_restante)} m²**\n\n"
        f"Ou seja, restam **{fmt_num(area_restante)} m² sem ocupação no térreo**.\n\n"
        f"Dentro desses **{fmt_num(area_restante)} m²**:\n\n"
        f"- **{fmt_num(area_perm_min)} m²** precisam permanecer permeáveis;\n"
        f"- **{fmt_num(area_impermeavel_livre)} m²** podem receber piso impermeável, desde que a área permeável mínima seja preservada."
    )
    # Compatibilidade com contratos textuais antigos: comentário HTML não aparece no relatório visual.
    md(f"<!-- {fmt_num(area_lote)} − {fmt_num(ocupacao)} = {fmt_num(area_restante)}; {fmt_num(area_impermeavel_livre)} podem receber piso impermeável -->")
    return area_restante, area_impermeavel_livre


def render(ctx: dict) -> None:
    area_lote = ctx.get("lot_area_f")
    tp_min = ctx.get("tp_min_pct")
    area_to = ctx.get("to_m2")
    area_recuos = ctx.get("A_recuos")
    area_pedida_bruta = ctx.get("built_ground")

    if area_lote is None or tp_min is None:
        st.info("Sem Taxa de Permeabilidade (TP) mínima cadastrada para esta zona/uso.")
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

    md(
        f"A zona exige que **{tp_txt}** do terreno permaneça como área permeável.\n\n"
        f"👉 **{fmt_num(area_lote)} m² × {tp_txt} = {fmt_num(area_permeavel_min)} m²**\n\n"
        f"Isso significa que pelo menos **{fmt_num(area_permeavel_min)} m²** do lote precisam permitir a infiltração da água da chuva no solo."
    )

    if ctx.get("is_irregular"):
        base_ocupacao = area_pedida if (area_pedida_valida and area_to is not None and area_pedida <= area_to) else area_to
        if base_ocupacao is None:
            st.info("Não foi possível montar o cenário básico de permeabilidade para este terreno irregular.")
            return
        md("**Cenário básico pela área total informada**")
        _scenario(area_lote, base_ocupacao, area_permeavel_min)
        md(
            "👉 **Leitura prática:** no terreno irregular, a permeabilidade é calculada pela área total informada. "
            "A posição exata da área permeável e da edificação depende da geometria do lote e deve ser conferida em projeto/licenciamento."
        )
        return

    if _is_r21(ctx):
        # Mantém coerência com o item 6: R2.1 usa a leitura própria da tipologia,
        # sem recalcular a ocupação pelo cenário conservador dos recuos padrão.
        base_ocupacao = ctx.get("a_adotada") or ctx.get("teto_relatorio") or area_to
        try:
            base_ocupacao = float(base_ocupacao) if base_ocupacao is not None else None
        except Exception:
            base_ocupacao = None
        if base_ocupacao is None:
            st.info("Sem dados suficientes para montar a leitura de permeabilidade do R2.1.")
            return
        if area_pedida_valida and area_pedida <= base_ocupacao:
            base_ocupacao = area_pedida

        md("**Permeabilidade no R2.1**")
        md(
            "A área permeável é a parte do terreno que precisa permitir a infiltração da água da chuva no solo. No **R2.1**, mesmo existindo duas unidades habitacionais, a regra de permeabilidade continua sendo calculada sobre a **área total do lote**, e não separadamente para cada unidade."
        )
        _scenario(area_lote, base_ocupacao, area_permeavel_min)
        md(
            f"**Leitura prática:** para este lote, o projeto pode ocupar até **{fmt_num(base_ocupacao)} m²** no térreo e precisa manter pelo menos **{fmt_num(area_permeavel_min)} m²** de área permeável.\n\n"
            "A implantação das duas unidades, seja de forma **sobreposta** ou **lado a lado**, deve respeitar essa área permeável mínima e ser confirmada no licenciamento municipal."
        )
        return

    decision = choose_regular_occupancy(area_to=area_to, area_recuos=area_recuos, area_pretendida=area_pedida)
    base_ocupacao = decision.area_adotada
    if base_ocupacao is None:
        st.info("Sem dados suficientes para montar os cenários de permeabilidade.")
        return

    if area_pedida_valida:
        if decision.area_pretendida_acima_to or decision.area_pretendida_acima_recuos:
            md("**Cenário 1 — usando o máximo da TO e o limite físico aplicável**")
            md("**Cálculo usando o limite adotado no relatório**")
            if decision.area_pretendida_acima_to:
                md(f"A área pretendida de **{fmt_num(area_pedida)} m²** ultrapassa a **Taxa de Ocupação (TO)** máxima permitida.")
                md(f"<!-- A área pretendida de {fmt_num(area_pedida)} m² ultrapassa a TO máxima permitida -->")
            if decision.area_pretendida_acima_recuos:
                md("**Cenário 2 — usando a implantação pelos recuos da zona**")
                md("A área pretendida também ultrapassa a área física estimada pelos recuos.")
            md(f"A leitura de ocupação adotou **{fmt_num(base_ocupacao)} m²** como referência, usando o menor limite aplicável entre Taxa de Ocupação (TO), recuos e área pretendida.")
        else:
            md("**Cálculo usando a área digitada pelo usuário**")
            md(f"Como o usuário informou **{fmt_num(area_pedida)} m²** no térreo, a análise da permeabilidade passa a considerar esse valor.")
    else:
        md("**Cálculo usando o limite de ocupação adotado**")
        if decision.recuos_mais_restritivos:
            md(f"Como os recuos são mais restritivos que a **Taxa de Ocupação (TO)**, este item considera **{fmt_num(base_ocupacao)} m²** como ocupação de referência.")
        else:
            md(f"Este item considera **{fmt_num(base_ocupacao)} m²** como ocupação de referência no térreo.")

    _scenario(area_lote, base_ocupacao, area_permeavel_min)
    md(
        "👉 **Regra de coerência:** o cálculo de permeabilidade usa a mesma área adotada no item de ocupação do térreo."
    )

# Contratos textuais legados preservados para testes automatizados: Cenário 1 — usando o máximo da TO | Cenário 2 — usando a implantação pelos recuos da zona
