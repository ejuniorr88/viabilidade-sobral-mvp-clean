from __future__ import annotations

from .common import md


def render(ctx: dict) -> None:
    md(
        "Além das regras do lote, a legislação também traz medidas mínimas para alguns ambientes da edificação. "
        "Isso vale para itens como sala, quartos, cozinha, banheiro, área de serviço, garagem e escada."
    )
    ctx['render_quadro_tecnico']()
