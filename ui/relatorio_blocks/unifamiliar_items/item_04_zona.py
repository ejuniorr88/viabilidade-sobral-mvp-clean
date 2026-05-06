from __future__ import annotations

from .common import md


def render(ctx: dict) -> None:
    # Mantém a referência a description_text porque o texto da zona vem dessa coluna quando disponível.
    md(
        "Todo terreno está inserido em uma zona, e cada zona pode ter regras, restrições e critérios próprios de uso e ocupação. "
        "Quando o terreno está localizado em área urbana com zoneamento definido, podem existir regras, restrições e critérios próprios de uso e ocupação. "
        "Nas áreas urbanas, essas informações normalmente ajudam a definir o que pode ser construído, quanto pode ocupar no térreo, quanto precisa ficar livre e o porte da edificação. "
        "Já em áreas rurais ou em zonas com tratamento especial, nem sempre existem parâmetros urbanísticos numéricos definidos da mesma forma. "
        "Nesses casos, a análise ficará restrita aos critérios aplicáveis do Código de Ordenamento Urbano e às demais regras específicas que incidirem sobre a área."
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
