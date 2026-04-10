from __future__ import annotations

from .common import md, fmt_num


def render(ctx: dict) -> None:
    md("Aqui estão os dados principais usados nesta análise:")
    md(
        f"- **Uso informado:** {ctx['uso_label']}\n"
        f"- **Área do terreno:** {fmt_num(ctx['A'])} m²\n"
        f"- **Dimensões:** {fmt_num(ctx['W'])} m × {fmt_num(ctx['D'])} m\n"
        f"- **Zona:** {ctx['zone']}\n"
        f"- **Subzona / setor:** {ctx['subzone_code']}\n"
        f"- **Tipo de lote:** {ctx['tipo_lote']}\n"
        f"- **Via:** {ctx['via']}\n"
        f"- **Tipo de via:** {ctx['via_tipo']}"
    )
    md("Essas informações são a base de todo o relatório.")
