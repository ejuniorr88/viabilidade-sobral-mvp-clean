from __future__ import annotations
from . import common
from ..quadro_tecnico import render_quadro_tecnico

def render(ctx):
    common.st.markdown("**Além das regras do lote, a legislação também traz medidas mínimas para alguns ambientes da edificação. Isso vale para itens como sala, quartos, cozinha, banheiro, área de serviço, garagem e escada.**")
    render_quadro_tecnico()
