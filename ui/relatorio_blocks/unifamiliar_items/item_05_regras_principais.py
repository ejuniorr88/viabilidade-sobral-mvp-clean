from __future__ import annotations

from .common import md, fmt_pct, fmt_num


def render(ctx: dict) -> None:
    md(
        "Depois de entender a zona, o próximo passo é ver as regras básicas do lote.\n\n"
        "Para este terreno, vale olhar principalmente:\n\n"
        "- ocupação máxima no térreo\n"
        "- área que precisa ficar livre\n"
        "- recuos\n"
        "- altura máxima\n"
        "- potencial total de construção"
    )
    linhas = [
        f"- **TO máxima:** {fmt_pct(ctx['to_max'])}",
        f"- **TP mínima:** {fmt_pct(ctx['tp_min'])}",
        f"- **IA máximo:** {fmt_num(ctx['ia_max']) if ctx['ia_max'] is not None else '—'}",
        f"- **IA mínimo:** {ctx['ia_min_texto']}",
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
    md("Essas são as regras que mais impactam o projeto.")
