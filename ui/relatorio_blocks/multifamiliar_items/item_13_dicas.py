from __future__ import annotations
from . import common

def render(ctx):
    common._render_dicas_valiosas(ctx['multi_tipo'], ctx['use_type_code'])
