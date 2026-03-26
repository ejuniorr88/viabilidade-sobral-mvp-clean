from __future__ import annotations

from .common import md


def render(ctx: dict) -> None:
    if ctx['desc'] and ctx['desc'].get("description_text"):
        md(f"**{ctx['zone_title']}**")
        md(str(ctx['desc'].get("description_text")))
    else:
        md(
            f"- **Zona:** {ctx['zone'] or '—'}\n"
            f"- **Via do terreno:** {ctx['via']}\n"
            f"- **Tipo de via:** {ctx['via_tipo']}"
        )
    md("**É essa leitura da zona que ajuda a entender o que pode ser implantado no lote e com qual porte.**")
