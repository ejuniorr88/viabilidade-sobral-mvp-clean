from __future__ import annotations

from .common import md


def render(ctx: dict) -> None:
    md(
        "A análise não termina dentro do lote. Também existem regras para calçada, acesso ao imóvel, rebaixo de meio-fio e relação do lote com a rua. "
        "As figuras abaixo ajudam a visualizar esse padrão."
    )
    ctx['render_figuras_anexo_v'](ctx['rule'], is_corner=ctx['is_corner'])
