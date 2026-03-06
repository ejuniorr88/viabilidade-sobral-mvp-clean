"""Blocos reutilizáveis do relatório."""

from .quadro_tecnico import render_quadro_tecnico
from .dicas_valiosas import render_dicas_valiosas
from .figuras_anexo_v import render_figuras_anexo_v
from .multifamiliar_guia import render_multifamiliar_guia

__all__ = [
    "render_quadro_tecnico",
    "render_dicas_valiosas",
    "render_figuras_anexo_v",
    "render_multifamiliar_guia",
]
