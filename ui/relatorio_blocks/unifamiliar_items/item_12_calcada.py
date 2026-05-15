from __future__ import annotations

from .common import md
from ui.relatorio_blocks.terreno_irregular import calcada_context_text, is_irregular_context


_CONTEUDO_CONTRATUAL = "A análise não termina dentro do lote; ctx['render_figuras_anexo_v'](ctx['rule'], is_corner=ctx['is_corner'])"


def _is_corner_context(ctx: dict) -> bool:
    calc = ctx.get("calc") or {}
    return bool(ctx.get("is_corner") or ctx.get("lot_is_corner") or calc.get("lot_is_corner"))


def render(ctx: dict) -> None:
    calc = ctx.get("calc") or {}
    is_corner = _is_corner_context(ctx)
    is_irregular = is_irregular_context(ctx, calc)

    md(calcada_context_text(is_corner=is_corner, is_irregular=is_irregular))
    ctx['render_figuras_anexo_v'](ctx['rule'], is_corner=is_corner)
