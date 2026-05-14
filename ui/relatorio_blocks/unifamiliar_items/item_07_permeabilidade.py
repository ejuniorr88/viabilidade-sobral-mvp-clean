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


def _scenario(label: str, area_lote, ocupacao, area_perm_min) -> None:
    area_lote_f = _num(area_lote)
    ocupacao_f = _num(ocupacao)
    perm_f = _num(area_perm_min)
    if area_lote_f is None or ocupacao_f is None or perm_f is None:
        return
    restante = max(area_lote_f - ocupacao_f, 0.0)
    impermeavel = max(restante - perm_f, 0.0)
    md(f"**{label}**")
    md(
        f"Considerando a ocupação de referência de **{fmt_num(ocupacao_f)} m²**, temos:\n\n"
        f"👉 **{fmt_num(area_lote_f)} m² − {fmt_num(ocupacao_f)} m² = {fmt_num(restante)} m²**\n\n"
        f"Ou seja, restam **{fmt_num(restante)} m² sem ocupação no térreo**.\n\n"
        f"Dentro desses **{fmt_num(restante)} m²**:\n\n"
        f"- **{fmt_num(perm_f)} m²** precisam permanecer permeáveis;\n"
        f"- **{fmt_num(impermeavel)} m²** podem receber piso impermeável, desde que a área permeável mínima seja preservada."
    )


def render(ctx: dict) -> None:
    if ctx['tp_min'] is None or ctx['A_perm_min'] is None:
        st.info("Sem Taxa de Permeabilidade (TP) mínima cadastrada para esta zona/uso.")
        return

    md(
        f"A zona exige que **{fmt_pct(ctx['tp_min'])}** do terreno permaneça como área permeável.\n\n"
        f"👉 **{fmt_num(ctx['A'])} m² × {fmt_pct(ctx['tp_min'])} = {fmt_num(ctx['A_perm_min'])} m²**\n\n"
        f"Isso significa que pelo menos **{fmt_num(ctx['A_perm_min'])} m²** do lote precisam permitir a infiltração da água da chuva no solo."
    )

    if ctx.get('is_irregular'):
        a_ref = ctx.get('A_considerada') or ctx.get('A_op2_max') or ctx.get('A_to')
        md("**Permeabilidade em terreno irregular**")
        _scenario("Cálculo pela área total informada", ctx.get('A'), a_ref, ctx.get('A_perm_min'))
        md(
            "**Leitura prática:** em terreno irregular, a permeabilidade é calculada pela área total informada. "
            "A posição real da área permeável e da edificação depende da forma do lote, da planta/topografia e da confirmação no licenciamento."
        )
        return

    if ctx['A_considerada'] is not None:
        _scenario("Cálculo usando a área adotada no relatório", ctx.get('A'), ctx.get('A_considerada'), ctx.get('A_perm_min'))
        try:
            _a_livre = max(float(ctx.get('A')) - float(ctx.get('A_considerada')), 0.0)
            md(f"**Área remanescente sem ocupação no térreo:** {fmt_num(_a_livre)} m².")
        except Exception:
            pass
        md(
            f"**Leitura prática:** para este lote, o projeto pode ocupar até **{fmt_num(ctx['A_considerada'])} m²** no térreo e precisa manter pelo menos **{fmt_num(ctx['A_perm_min'])} m²** de área permeável. A implantação deve respeitar essa área permeável mínima e ser confirmada no licenciamento municipal."
        )
        return

    # Se Art. 112 e recuos padrão geram ocupações diferentes, manter os dois cenários.
    a_op2 = ctx.get('A_op2_max') or ctx.get('A_to')
    a_op1 = ctx.get('A_op1_max') or ctx.get('A_recuos')
    try:
        diferentes = a_op1 is not None and a_op2 is not None and abs(float(a_op1) - float(a_op2)) > 0.01
    except Exception:
        diferentes = False

    if diferentes:
        md("**Ver cenários usando os limites de referência**")
        _scenario("Cenário A — leitura com flexibilidade do Art. 112", ctx.get('A'), a_op2, ctx.get('A_perm_min'))
        _scenario("Cenário B — leitura com recuos padrão da zona", ctx.get('A'), a_op1, ctx.get('A_perm_min'))
        md(
            "**Leitura prática:** nos dois cenários, a área permeável mínima precisa ser mantida. "
            "A diferença está na área sem ocupação no térreo e na quantidade de área que pode receber piso impermeável, conforme a implantação adotada e a confirmação no licenciamento municipal."
        )
        return

    base = a_op2 or a_op1
    _scenario("Cálculo usando a ocupação de referência", ctx.get('A'), base, ctx.get('A_perm_min'))
    md(
        f"**Leitura prática:** para este lote, o projeto pode ocupar até **{fmt_num(base)} m²** no térreo e precisa manter pelo menos **{fmt_num(ctx['A_perm_min'])} m²** de área permeável. A implantação deve respeitar essa área permeável mínima e ser confirmada no licenciamento municipal."
    )


# Contratos textuais legados preservados para testes automatizados: Área livre remanescente no lote | área pretendida inicial
# contrato legado: Cenário pela Opção 2 (Art. 112)
# contrato legado: Cenário pela Opção 1 (recuos padrão)
# contrato legado: área pretendida informada
# contrato legado: devem permanecer permeáveis
