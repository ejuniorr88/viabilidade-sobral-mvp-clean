from __future__ import annotations


def render(ctx: dict) -> None:
    ctx['_render_dicas_valiosas'](ctx['multi_tipo'], ctx['use_type_code'])
