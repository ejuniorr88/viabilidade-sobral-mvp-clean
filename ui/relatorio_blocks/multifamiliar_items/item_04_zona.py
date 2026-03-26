from __future__ import annotations
from . import common

def render(ctx):
    common.st.markdown(
        "Todo terreno está inserido em uma zona, e cada zona pode ter regras, restrições e critérios próprios de uso e ocupação. Nas áreas urbanas, essas informações normalmente ajudam a definir o que pode ser construído, quanto pode ocupar no térreo, quanto precisa ficar livre e o porte da edificação. Já em áreas rurais ou em zonas com tratamento especial, nem sempre existem parâmetros urbanísticos numéricos definidos da mesma forma. Nesses casos, a análise ficará restrita aos critérios aplicáveis do Código de Ordenamento Urbano e às demais regras específicas que incidirem sobre a área."
    )
    desc = ctx["desc"]
    zona = ctx["zona"]
    if desc and desc.get("description_text"):
        title = str(desc.get("title") or zona).strip()
        if title.upper() == (zona or "").upper():
            zone_head = zona
        elif title.upper().startswith((zona or "").upper() + " —") or title.upper().startswith((zona or "").upper() + " -"):
            zone_head = title
        else:
            zone_head = f"{zona} — {title}"
        common.st.markdown(f"**{zone_head}**")
        common.st.markdown(str(desc.get("description_text")))
    else:
        common.st.markdown(
            f"- **Zona:** {zona or '—'}\n"
            f"- **Via do terreno:** {ctx['via']}\n"
            f"- **Tipo de via:** {ctx['via_tipo_txt'] or '—'}"
        )
    common.st.markdown("**É essa leitura da zona que ajuda a entender o que pode ser implantado no lote e com qual porte.**")
