from __future__ import annotations

from .common import md


def render(ctx: dict) -> None:
    # Mantém a referência a description_text porque o texto da zona vem dessa coluna quando disponível.
    md(
        "Todo terreno está inserido em uma zona. Essa zona ajuda a entender, de forma prática, "
        "o que pode ser feito no lote, quanto pode ocupar no térreo, quanto precisa ficar livre e quais cuidados "
        "devem ser observados no projeto. Em zonas especiais, ambientais, patrimoniais ou de proteção da paisagem, "
        "a análise pode exigir mais confirmação no licenciamento antes de qualquer aprovação."
    )

    if ctx['desc'] and ctx['desc'].get("description_text"):
        
        zone_title = ctx.get('zone_title') or ctx.get('zone_label') or ctx.get('zone_sigla') or ctx.get('zone') or '—'
        if str(zone_title).strip().lower() not in ('', 'none', 'null'):
            md(f"**{zone_title}**")
        md(str(ctx['desc'].get("description_text")))
    else:
        md(
            f"- **Zona:** {ctx['zone'] or '—'}\n"
            f"- **Via do terreno:** {ctx['via']}\n"
            f"- **Tipo de via:** {ctx['via_tipo']}"
        )

    md("**É essa leitura da zona que ajuda a entender o que pode ser implantado no lote e com qual porte.**")
