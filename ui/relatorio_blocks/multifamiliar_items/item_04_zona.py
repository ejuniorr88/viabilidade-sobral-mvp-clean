from __future__ import annotations
from . import common


def _clean(value, fallback=""):
    s = str(value or "").strip()
    if not s or s.lower() in {"none", "null", "nan", "—", "-"}:
        return fallback
    return s


def _zona_titulo(ctx: dict, desc: dict | None) -> str:
    zona = _clean(ctx.get("zona"))
    subzona = _clean(ctx.get("subzona"))
    zone_label = _clean(ctx.get("zone_label"))
    desc_title = _clean((desc or {}).get("title"))

    if desc_title:
        if zona and desc_title.upper().startswith(zona.upper()):
            return desc_title
        if zona:
            return f"{zona} — {desc_title}"
        return desc_title

    if zona and subzona and subzona.upper() not in {"PADRAO", zona.upper()}:
        return f"{zona} — {subzona.replace('_', ' ')}"
    return zone_label or zona or "—"


def render(ctx):
    common.st.markdown(
        "Todo terreno está inserido em uma zona. Essa zona ajuda a entender, de forma prática, "
        "o que pode ser feito no lote, quanto pode ocupar no térreo, quanto precisa ficar livre e quais cuidados "
        "devem ser observados no projeto. Em zonas especiais, ambientais, patrimoniais ou de proteção da paisagem, "
        "a análise pode exigir mais confirmação no licenciamento antes de qualquer aprovação."
    )
    desc = ctx.get("desc")
    if desc and desc.get("description_text"):
        zone_head = _zona_titulo(ctx, desc)
        if zone_head and zone_head != "—":
            common.st.markdown(f"**{zone_head}**")
        common.st.markdown(str(desc.get("description_text")))
    else:
        common.st.markdown(
            f"- **Zona:** {_zona_titulo(ctx, None)}\n"
            f"- **Via do terreno:** {_clean(ctx.get('via'), '—')}\n"
            f"- **Tipo de via:** {_clean(ctx.get('via_tipo_txt'), '—')}"
        )
    common.st.markdown("**É essa leitura da zona que ajuda a entender o que pode ser implantado no lote e com qual porte.**")
