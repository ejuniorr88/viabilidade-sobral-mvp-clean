from __future__ import annotations

from .common import md, fmt_num
from ui.relatorio_blocks.terreno_irregular import dimensoes_text, aviso_texto

# LEGACY_IRREGULAR_CONTRACT_TEXT: Terreno irregular – cálculo pela área total informada
# LEGACY_IRREGULAR_CONTRACT_TEXT: Por se tratar de terreno irregular, os cálculos foram feitos com base na área total informada


def render(ctx: dict) -> None:
    md("Aqui estão os dados principais usados nesta análise:")
    dimensoes = (
        dimensoes_text(ctx.get("A"))
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
        md(f"> **Observação técnica:** {aviso_texto()}")
    md("Essas informações são a base de todo o relatório.")
