from __future__ import annotations
from . import common

def render(ctx):
    common.st.markdown("Aqui entram:")
    common.st.markdown(
        f"- **Uso informado:** {ctx['uso_label']}\n"
        f"- **Área do terreno:** {common._fmt_num(ctx['lot_area_f'])} m²\n"
        f"- **Dimensões:** {common._fmt_num(ctx['lot_front'])} m × {common._fmt_num(ctx['lot_depth'])} m\n"
        f"- **Zona:** {ctx['zona'] or '—'}\n"
        f"- **Subzona / setor:** {ctx['subzona']}\n"
        f"- **Tipo de lote:** {ctx['tipo_lote']}\n"
        f"- **Via:** {ctx['via']}\n"
        f"- **Tipo de via:** {ctx['via_tipo_txt'] or '—'}"
    )
    common.st.markdown("**Essas informações são a base de toda a leitura do relatório.**")
