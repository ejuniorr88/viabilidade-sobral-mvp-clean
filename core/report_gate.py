from __future__ import annotations

from typing import Any, Dict


def should_block_multifamiliar(calc_ref: Dict[str, Any], *, rule, should_block_multifamiliar_preview_func) -> bool:
    return should_block_multifamiliar_preview_func(calc_ref, rule=rule)


def should_block_unifamiliar(calc_ref: Dict[str, Any], *, should_block_unifamiliar_preview_func) -> bool:
    return should_block_unifamiliar_preview_func(calc_ref)


def render_multifamiliar_preview(*, calc, rule, render_multifamiliar_inadequado_preview_func) -> None:
    render_multifamiliar_inadequado_preview_func(calc=calc, rule=rule)


def render_unifamiliar_preview(calc_ref: Dict[str, Any], *, render_unifamiliar_inadequado_preview_func) -> None:
    render_unifamiliar_inadequado_preview_func(calc_ref)
