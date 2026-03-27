from __future__ import annotations
from . import common
from ..figuras_anexo_v import render_figuras_anexo_v

def render(ctx):
    common.st.markdown("**A análise do terreno não termina dentro do lote. Também existem regras para calçada, acesso ao imóvel, rebaixo de meio-fio e relação com a rua.**")
    render_figuras_anexo_v(ctx['rule'] or {}, is_corner=bool(common.st.session_state.get('lot_is_corner') or ctx['calc'].get('lot_is_corner')))
