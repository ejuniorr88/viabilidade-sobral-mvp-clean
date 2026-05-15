"""Camada leve de regras urbanísticas auxiliares.

Criada para centralizar regras comuns sem reescrever o fluxo consolidado do relatório.
"""

from .common import (
    OccupancyDecision,
    choose_regular_occupancy,
    to_float,
)

__all__ = ["OccupancyDecision", "choose_regular_occupancy", "to_float"]
