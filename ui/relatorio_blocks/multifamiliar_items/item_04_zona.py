from __future__ import annotations

from .common import md


def render(ctx: dict) -> None:
    if ctx['desc'] and ctx['desc'].get('description_text'):
        title = str(ctx['desc'].get('title') or ctx['zona']).strip()
        if title.upper() == (ctx['zona'] or '').upper():
            zone_head = ctx['zona']
        elif title.upper().startswith((ctx['zona'] or '').upper() + ' —') or title.upper().startswith((ctx['zona'] or '').upper() + ' -'):
            zone_head = title
        else:
            zone_head = f"{ctx['zona']} — {title}"
        md(f"**{zone_head}**")
        md(str(ctx['desc'].get('description_text')))
    else:
        md(
            f"- **Zona:** {ctx['zona'] or '—'}\n"
            f"- **Via do terreno:** {ctx['via']}\n"
            f"- **Tipo de via:** {ctx['via_tipo_txt'] or '—'}"
        )
    md("**É essa leitura da zona que ajuda a entender o que pode ser implantado no lote e com qual porte.**")
