from __future__ import annotations

from .common import md


def render(ctx: dict) -> None:
    md("**A análise do terreno não termina dentro do lote. Também existem regras para calçada, acesso ao imóvel, rebaixo de meio-fio e relação com a rua.**")
    ctx['render_figuras_anexo_v'](ctx['rule'] or {}, is_corner=ctx['is_corner'])
