from __future__ import annotations

from ui.lote import render_lote_section


def render_lot_inputs():
    """Mantém o bloco consolidado de entrada do lote, agora modularizado
    no namespace ui.lot sem alterar layout nem comportamento."""
    return render_lote_section()
