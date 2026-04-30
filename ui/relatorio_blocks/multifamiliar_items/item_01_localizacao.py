from __future__ import annotations

from .common import md, fmt_num


def render(ctx: dict) -> None:
    md("Aqui estão os dados principais usados nesta análise:")
    dimensoes = (
        "Terreno irregular – cálculo pela área total informada"
        if ctx.get("is_irregular")
        else f"{fmt_num(ctx['W'])} m × {fmt_num(ctx['D'])} m"
    )
    md(
        f"- **Uso informado:** {ctx['uso_label']}\n"
        f"- **Área do terreno:** {fmt_num(ctx['A'])} m²\n"
        f"- **Dimensões/forma:** {dimensoes}\n"
        f"- **Zona:** {ctx['zone']}\n"
        f"- **Subzona / setor:** {ctx['subzone_code']}\n"
        f"- **Tipo de lote:** {ctx['tipo_lote']}\n"
        f"- **Via:** {ctx['via']}\n"
        f"- **Tipo de via:** {ctx['via_tipo']}"
    )
    if ctx.get("is_irregular"):
        md(
            "> **Observação técnica:** Por se tratar de terreno irregular, os cálculos foram feitos com base na área total informada. "
            "A implantação da edificação deve ser conferida em projeto, considerando a geometria real do lote, divisas, recuos e condicionantes locais."
        )
    md("Essas informações são a base de todo o relatório.")
