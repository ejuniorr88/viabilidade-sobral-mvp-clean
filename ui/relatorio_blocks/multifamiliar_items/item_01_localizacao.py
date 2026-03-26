from __future__ import annotations

from .common import md


def render(ctx: dict) -> None:
    md("Aqui entram:")
    md(
        f"- **Uso informado:** {ctx['uso_label']}\n"
        f"- **Área do terreno:** {ctx['_fmt_num'](ctx['lot_area_f'])} m²\n"
        f"- **Dimensões:** {ctx['_fmt_num'](ctx['lot_front'])} m × {ctx['_fmt_num'](ctx['lot_depth'])} m\n"
        f"- **Zona:** {ctx['zona'] or '—'}\n"
        f"- **Subzona / setor:** {ctx['subzona']}\n"
        f"- **Tipo de lote:** {ctx['tipo_lote']}\n"
        f"- **Via:** {ctx['via']}\n"
        f"- **Tipo de via:** {ctx['via_tipo_txt'] or '—'}"
    )
    md("**Essas informações são a base de toda a leitura do relatório.**")
