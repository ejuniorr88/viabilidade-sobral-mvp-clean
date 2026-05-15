from __future__ import annotations

from . import common
from ..figuras_anexo_v import render_figuras_anexo_v
from ui.relatorio_blocks.terreno_irregular import calcada_context_text, is_irregular_context


_CONTEUDO_CONTRATUAL = "A análise do terreno não termina dentro do lote; rebaixo de meio-fio"


def _is_corner_context(ctx: dict) -> bool:
    calc = ctx.get("calc") or {}
    return bool(
        common.st.session_state.get("lot_is_corner")
        or ctx.get("is_corner")
        or ctx.get("lot_is_corner")
        or calc.get("lot_is_corner")
    )


def render(ctx):
    calc = ctx.get("calc") or {}
    is_corner = _is_corner_context(ctx)
    is_irregular = is_irregular_context(ctx, calc)

    common.st.markdown(f"**{calcada_context_text(is_corner=is_corner, is_irregular=is_irregular)}**")
    render_figuras_anexo_v(ctx['rule'] or {}, is_corner=is_corner)
