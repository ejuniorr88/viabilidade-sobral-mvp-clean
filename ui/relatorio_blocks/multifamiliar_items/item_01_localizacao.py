from __future__ import annotations
from . import common


def _ctx_value(ctx, *keys, default=None):
    for key in keys:
        if key in ctx:
            value = ctx.get(key)
            if value not in (None, ""):
                return value
    return default


def render(ctx):
    common.st.markdown("Aqui entram:")

    is_irregular = bool(ctx.get("is_irregular"))
    lot_front = _ctx_value(ctx, "lot_front", "W", default=0)
    lot_depth = _ctx_value(ctx, "lot_depth", "D", default=0)
    lot_area = _ctx_value(ctx, "lot_area_f", "A", default=0)

    dimensoes = (
        "Terreno irregular – cálculo pela área total informada"
        if is_irregular
        else f"{common._fmt_num(lot_front)} m × {common._fmt_num(lot_depth)} m"
    )

    common.st.markdown(
        f"- **Uso informado:** {ctx.get('uso_label', '—')}\n"
        f"- **Área do terreno:** {common._fmt_num(lot_area)} m²\n"
        f"- **Dimensões/forma:** {dimensoes}\n"
        f"- **Zona:** {ctx.get('zona') or ctx.get('zone') or '—'}\n"
        f"- **Subzona / setor:** {ctx.get('subzona') or ctx.get('subzone_code') or '—'}\n"
        f"- **Tipo de lote:** {ctx.get('tipo_lote') or '—'}\n"
        f"- **Via:** {ctx.get('via') or '—'}\n"
        f"- **Tipo de via:** {ctx.get('via_tipo_txt') or ctx.get('via_tipo') or '—'}"
    )
    if is_irregular:
        common.st.markdown(
            "> **Observação técnica:** Por se tratar de terreno irregular, os cálculos foram feitos com base na área total informada. "
            "A implantação da edificação deve ser conferida em projeto, considerando a geometria real do lote, divisas, recuos e condicionantes locais."
        )
    common.st.markdown("**Essas informações são a base de toda a leitura do relatório.**")
