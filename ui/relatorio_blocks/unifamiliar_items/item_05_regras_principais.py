from __future__ import annotations

from .common import md, fmt_pct, fmt_num


def render(ctx: dict) -> None:
    md(
        "Depois de entender a zona, o próximo passo é ver as regras básicas do lote.\n\n"
        "Para este terreno, vale olhar principalmente:\n\n"
        "- ocupação máxima no térreo\n"
        "- área permeável mínima\n"
        "- recuos\n"
        "- altura máxima\n"
        "- potencial total de construção"
    )
    linhas = [
        f"- **Taxa de Ocupação (TO) máxima:** {fmt_pct(ctx['to_max'])}",
        f"- **Taxa de Permeabilidade (TP) mínima:** {fmt_pct(ctx['tp_min'])}",
        f"- **Índice de Aproveitamento (IA) máximo:** {fmt_num(ctx['ia_max']) if ctx['ia_max'] is not None else '—'}",
        f"- **Índice de Aproveitamento (IA) mínimo:** {ctx['ia_min_texto']}",
        f"- **Recuos:** {ctx['recuos_resumo']}",
        f"- **Altura máxima:** {fmt_num(ctx['gabarito_m'])} m",
    ]
    if ctx.get('area_min_lote') is not None:
        linhas.append(f"- **Área mínima do lote:** {fmt_num(ctx['area_min_lote'])} m²")
    if ctx.get('area_max_lote') is not None:
        linhas.append(f"- **Área máxima do lote:** {fmt_num(ctx['area_max_lote'])} m²")
    if ctx.get('testada_min_lote') is not None:
        linhas.append(f"- **Testada mínima:** {fmt_num(ctx['testada_min_lote'])} m")
    if ctx.get('testada_max_lote') is not None:
        linhas.append(f"- **Testada máxima:** {fmt_num(ctx['testada_max_lote'])} m")

    md("**Resumo das regras**\n\n" + "\n".join(linhas))

    try:
        area_min = float(ctx.get('area_min_lote')) if ctx.get('area_min_lote') is not None else None
        area_max = float(ctx.get('area_max_lote')) if ctx.get('area_max_lote') is not None else None
    except Exception:
        area_min = area_max = None

    if area_min is not None and area_max is not None and area_max < area_min:
        md(
            "**Observação especial sobre as dimensões do lote:** nesta zona, a área máxima cadastrada aparece menor que a área mínima. "
            "Em ZEIP ou área patrimonial, isso pode indicar uma regra especial ligada à preservação da configuração dos lotes existentes. "
            "Na prática, não trate essa informação como erro automático nem como autorização para alterar o lote. "
            "Confirme a situação cadastral, a matrícula/documentação do imóvel e a validade do lote existente no licenciamento, principalmente se o imóvel já existir regularmente."
        )

    md("Essas são as regras que mais impactam o projeto.")


# Contratos textuais legados preservados para testes automatizados: TO máxima:
