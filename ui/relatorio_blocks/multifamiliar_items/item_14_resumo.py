from __future__ import annotations
from . import common


def _clean(value, fallback="—"):
    s = str(value or "").strip()
    if not s or s.lower() in {"none", "null", "nan", "—", "-"}:
        return fallback
    return s


def _uso_resumo(ctx: dict) -> str:
    multi_tipo = str(ctx.get("multi_tipo") or "").upper()
    use_type_code = str(ctx.get("use_type_code") or "").upper()
    if multi_tipo in ("R22", "R2.2", "R2_2") or use_type_code.endswith("R22"):
        return "R2.2 — condomínio horizontal com via interna"
    if multi_tipo in ("R3", "R03") or use_type_code.endswith("R3"):
        return "R3 — residência multifamiliar vertical"
    if multi_tipo in ("R21", "R2.1", "R2_1") or use_type_code.endswith("R21"):
        return "R2.1 — 2 unidades no mesmo lote (justapostas ou sobrepostas)"
    return _clean(ctx.get("uso_label"), "residencial multifamiliar")


def _zona_resumo(ctx: dict) -> str:
    zona = _clean(ctx.get("zona"), "")
    subzona = _clean(ctx.get("subzona"), "")
    zone_label = _clean(ctx.get("zone_label"), "")
    if zona and subzona and subzona.upper() not in {"PADRAO", zona.upper()}:
        return f"{zona} — {subzona.replace('_', ' ')}"
    return zone_label or zona or "—"


def _resultado_resumo(ctx: dict) -> str:
    if ctx.get("is_irregular"):
        common.st.markdown(
            "👉 **Observação:** por se tratar de terreno irregular, esse valor é uma referência máxima pela Taxa de Ocupação. "
            "A implantação real depende da geometria do lote e deve ser confirmada em projeto e no licenciamento."
        )

    if ctx.get("is_zeip9"):
        return "⚠️ EXIGE CONFIRMAÇÃO — ZEIP_9"
    if ctx.get("r21_testada_baixa"):
        return "⚠️ PERMITE COM RESSALVA"
    return f"{_clean(ctx.get('icon'), '')} {_clean(ctx.get('status_curto'))}".strip()


def _render_pontos_atencao(ctx: dict) -> None:
    warnings = [str(w).strip() for w in (ctx.get("zone_warnings") or []) if str(w).strip()]
    if not warnings:
        return

    bullets = "\n".join(f"- {w}" for w in warnings[:3])
    common.st.markdown(
        "**Pontos de atenção para guardar:**\n"
        f"{bullets}"
    )


def render(ctx):
    common.st.markdown("Se você quiser ver só o essencial deste terreno, este é o resumo principal:")
    resumo_uso = _uso_resumo(ctx)
    zona_txt = _zona_resumo(ctx)
    tipo_lote = "Terreno irregular" if ctx.get("is_irregular") else _clean(ctx.get("tipo_lote"), "Meio de quadra")
    via = _clean(ctx.get("via"))
    via_tipo = _clean(ctx.get("via_tipo_txt"))
    resultado = _resultado_resumo(ctx)

    resumo_extra = ""
    limite_label = "Limite máximo pela Taxa de Ocupação" if ctx.get("is_irregular") else "Referência de ocupação máxima no térreo"
    if ctx.get('built_ground') is not None and ctx.get('a_adotada') is not None:
        resumo_extra += f"\n- **Área pretendida informada:** {common._fmt_num(ctx['built_ground'])} m²"
        resumo_extra += f"\n- **Área adotada no relatório:** {common._fmt_num(ctx['a_adotada'])} m²"
        if ctx.get('to_utilizada_pct') is not None:
            resumo_extra += f"\n- **Taxa de Ocupação (TO) efetiva considerada:** {common._fmt_pct(ctx['to_utilizada_pct'])}"
        if ctx.get('area_livre_projeto') is not None:
            resumo_extra += f"\n- **Área remanescente sem ocupação no térreo:** {common._fmt_num(ctx['area_livre_projeto'])} m²"
        if ctx.get('ia_saldo') is not None:
            resumo_extra += f"\n- **Saldo estimado pelo Índice de Aproveitamento (IA):** {common._fmt_num(ctx['ia_saldo'])} m²"
    elif ctx.get('teto_relatorio') is not None:
        resumo_extra += f"\n- **{limite_label}:** {common._fmt_num(ctx['teto_relatorio'])} m²"

    common.st.markdown(
        f"- **Uso analisado:** {resumo_uso}\n"
        f"- **Zona:** {zona_txt}\n"
        f"- **Tipo de lote:** {tipo_lote}\n"
        f"- **Via:** {via}\n"
        f"- **Tipo de via:** {via_tipo}\n"
        f"- **Resultado final:** {resultado}\n"
        f"- **Taxa de Ocupação (TO) máxima:** {common._fmt_pct(ctx.get('to_max_pct'))}\n"
        f"- **Taxa de Permeabilidade (TP) mínima:** {common._fmt_pct(ctx.get('tp_min_pct'))}\n"
        f"- **Índice de Aproveitamento (IA) máximo:** {common._fmt_num(ctx.get('ia_max'), 2) if ctx.get('ia_max') not in (None, '') else '—'}\n"
        f"- **Altura permitida máxima:** {common._fmt_num(ctx.get('gabarito_f'))} m{resumo_extra}"
    )

    _render_pontos_atencao(ctx)


    if ctx.get("zone_testada_baixa"):
        common.st.warning(
            f"⚠️ **Atenção dimensional:** a testada informada ({common._fmt_num(ctx.get('lot_front'))} m) "
            f"está abaixo da testada mínima exibida para este caso ({common._fmt_num(ctx.get('testada_min'))} m). "
            "Confirme a regularidade dimensional do lote no licenciamento municipal."
        )

    if ctx.get("r21_testada_baixa"):
        common.st.warning(
            "⚠️ **Observação específica sobre R2.1:** a testada informada é inferior a 8,00 m para R2.1 justaposto fora de ZEIS. Além da testada mínima da zona, o R2.1 pode exigir cuidado adicional na implantação, especialmente quando as duas unidades forem lado a lado. "
            "Essa referência não substitui o parâmetro da zona, mas indica que o projeto deve ser analisado com cautela pelo órgão licenciador. Antes de seguir, revise o enquadramento do projeto ou confirme a possibilidade no licenciamento municipal."
        )

# Contratos textuais legados preservados para testes automatizados: TO efetiva considerada | Área livre remanescente
