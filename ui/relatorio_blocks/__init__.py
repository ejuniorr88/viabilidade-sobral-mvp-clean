"""Blocos reutilizáveis do relatório.

Este pacote expõe funções de renderização usadas pelo ui/relatorio.py.
"""

from .quadro_tecnico import render_quadro_tecnico
from .dicas_valiosas import render_dicas_valiosas
from .figuras_anexo_v import render_figuras_anexo_v

# Multifamiliar (Fase 1 - Guia)
try:
    from .multifamiliar_guia import render_multifamiliar_guia
except Exception as e:  # pragma: no cover
    # Mantém import do app explícito e com erro amigável caso o módulo não exista
    def render_multifamiliar_guia(*args, **kwargs):
        raise ImportError(
            "Não foi possível importar render_multifamiliar_guia de ui/relatorio_blocks/multifamiliar_guia.py"
        ) from e

__all__ = [
    "render_quadro_tecnico",
    "render_dicas_valiosas",
    "render_figuras_anexo_v",
    "render_multifamiliar_guia",
]
