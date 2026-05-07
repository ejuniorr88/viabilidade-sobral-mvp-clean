from __future__ import annotations

from .common import md, fmt_num, fmt_pct


_EMPTY = {None, "", "—", "-"}


def _pick(ctx: dict, *keys, default=None):
    for key in keys:
        value = ctx.get(key)
        if value not in _EMPTY:
            return value
    return default


def _num(value):
    try:
        if value in _EMPTY:
            return None
        return float(value)
    except Exception:
        return None


def _fmt_pct_br(value) -> str:
    if value is None:
        return "—"
    return fmt_pct(value).replace(".", ",")


def _tipo_lote(ctx: dict) -> str:
    tipo = _pick(ctx, "tipo_lote")
    if tipo:
        return str(tipo)
    calc = ctx.get("calc") or {}
    if calc.get("lot_is_irregular") or ctx.get("is_irregular"):
        return "Terreno irregular"
    if calc.get("lot_is_corner") or ctx.get("is_corner"):
        return "Esquina"
    return "Meio de quadra"


def _zone_title(ctx: dict) -> str:
    title = _pick(ctx, "zone_title")
    if title:
        return str(title)
    zone = _pick(ctx, "zone_sigla", "zone", default="—")
    sub = _pick(ctx, "subzone_code")
    if sub and str(sub).upper() not in {"PADRAO", str(zone).upper()}:
        return f"{zone} — {str(sub).replace('_', ' ')}"
    return str(zone)


def render(ctx: dict) -> None:
    md("**Se você quiser ver só o essencial deste terreno, este é o resumo principal:**")

    area_lote = _num(_pick(ctx, "A", "area_lote", "lot_area_m2"))
    area_pedida = _num(_pick(ctx, "area_pedida", "built_ground"))
    area_considerada = _num(_pick(ctx, "A_considerada", "area_adotada"))
    ia_max = _num(_pick(ctx, "ia_max"))
    a_total = _num(_pick(ctx, "A_total", "area_total_max"))
    if a_total is None and area_lote is not None and ia_max is not None:
        a_total = area_lote * ia_max

    gabarito_m = _num(_pick(ctx, "gabarito_m", "altura_max"))
    a_to = _num(_pick(ctx, "A_to", "area_to_max"))
    a_perm_min = _num(_pick(ctx, "A_perm_min", "area_permeavel_min"))
    a_livre = _num(_pick(ctx, "A_livre", "area_livre"))
    if a_livre is None and area_lote is not None and area_considerada is not None:
        a_livre = area_lote - area_considerada

    to_projeto_pct = _num(_pick(ctx, "to_projeto_pct", "to_utilizada_pct"))
    if to_projeto_pct is None and area_lote not in (None, 0) and area_considerada is not None:
        to_projeto_pct = (area_considerada / area_lote) * 100.0

    a_ia_saldo = _num(_pick(ctx, "A_ia_saldo", "ia_saldo"))
    if a_ia_saldo is None and a_total is not None and area_considerada is not None:
        a_ia_saldo = a_total - area_considerada

    limite_real = _num(_pick(ctx, "A_teto_projeto", "A_op2_max", "A_op1_max", "A_to"))
    if limite_real is None:
        limite_real = a_to

    resumo_extra = ""
    limite_label = "Limite máximo pela Taxa de Ocupação" if bool(ctx.get("is_irregular")) else "Limite real de ocupação no térreo"
    if area_pedida is not None and area_considerada is not None:
        resumo_extra += f"\n- **Área pretendida informada:** {fmt_num(area_pedida)} m²"
        resumo_extra += f"\n- **Área adotada no relatório:** {fmt_num(area_considerada)} m²"
        if to_projeto_pct is not None:
            resumo_extra += f"\n- **TO efetiva considerada:** {_fmt_pct_br(to_projeto_pct)}"
        if a_livre is not None:
            resumo_extra += f"\n- **Área livre remanescente:** {fmt_num(a_livre)} m²"
        if a_ia_saldo is not None:
            resumo_extra += f"\n- **Saldo estimado pelo IA:** {fmt_num(a_ia_saldo)} m²"

    md(
        f"- **Uso analisado:** {_pick(ctx, 'uso_label', default='residência unifamiliar')}\n"
        f"- **Zona:** {_zone_title(ctx)}\n"
        f"- **Tipo de lote:** {_tipo_lote(ctx)}\n"
        f"- **Via:** {_pick(ctx, 'via', default='—')}\n"
        f"- **Tipo de via:** {_pick(ctx, 'via_tipo', default='—')}\n\n"
        f"- **TO máxima:** {fmt_pct(_pick(ctx, 'to_max'))}\n"
        f"- **TP mínima:** {fmt_pct(_pick(ctx, 'tp_min'))}\n"
        f"- **IA máximo:** {fmt_num(ia_max) if ia_max is not None else '—'}\n"
        f"- **Altura máxima:** {fmt_num(gabarito_m)} m\n\n"
        f"- **Área máxima no térreo pela TO:** {fmt_num(a_to)} m²\n"
        f"- **Área permeável mínima:** {fmt_num(a_perm_min)} m²\n"
        f"- **Área total máxima estimada:** {fmt_num(a_total)} m²"
        f"{resumo_extra}\n"
        f"- **{limite_label}:** {fmt_num(limite_real)} m²"
    )

    if area_pedida is not None and area_considerada is not None:
        if bool(ctx.get('excedeu_area')):
            md(
                f"👉 **Em resumo:** você informou **{fmt_num(area_pedida)} m²** no térreo, mas o relatório adotou **{fmt_num(area_considerada)} m²** para respeitar os limites urbanísticos do lote. "
                f"Com isso, a TO efetiva considerada ficou em **{_fmt_pct_br(to_projeto_pct)}**, a área livre remanescente em **{fmt_num(a_livre)} m²** e o saldo estimado pelo IA em **{fmt_num(a_ia_saldo)} m²**."
            )
        else:
            md(
                f"👉 **Em resumo:** o relatório considerou a área pretendida de **{fmt_num(area_considerada)} m²** no térreo. "
                f"Com isso, a TO efetiva considerada ficou em **{_fmt_pct_br(to_projeto_pct)}**, a área livre remanescente em **{fmt_num(a_livre)} m²** e o saldo estimado pelo IA em **{fmt_num(a_ia_saldo)} m²**."
            )
    else:
        if bool(ctx.get("is_irregular")):
            md(
                f"👉 **Em resumo:** pela Taxa de Ocupação, o limite máximo de referência é **{fmt_num(limite_real)} m²** no térreo. "
                f"Ainda assim, a implantação real depende da geometria do terreno e deve ser confirmada em projeto e no licenciamento. "
                f"Também é preciso manter pelo menos **{fmt_num(a_perm_min)} m²** permeáveis."
            )
        else:
            md(
                f"👉 **Em resumo:** você pode ocupar até **{fmt_num(limite_real)} m²** no térreo, "
                f"precisa manter pelo menos **{fmt_num(a_perm_min)} m²** permeáveis e respeitar os demais parâmetros urbanísticos."
            )
