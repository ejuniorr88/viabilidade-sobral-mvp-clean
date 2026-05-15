from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


def to_float(value: Any) -> Optional[float]:
    """Converte valores numéricos vindos do contexto do relatório com segurança."""
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None


@dataclass(frozen=True)
class OccupancyDecision:
    """Resultado comum para ocupação no térreo em lote regular.

    A decisão não altera parâmetros da zona; apenas escolhe a menor área aplicável
    entre TO, envelope físico por recuos e área pretendida válida.
    """

    area_to: Optional[float]
    area_recuos: Optional[float]
    area_pretendida: Optional[float]
    area_adotada: Optional[float]
    recuos_mais_restritivos: bool = False
    to_mais_restritiva: bool = False
    area_pretendida_acima_to: bool = False
    area_pretendida_acima_recuos: bool = False


def choose_regular_occupancy(
    *,
    area_to: Any,
    area_recuos: Any = None,
    area_pretendida: Any = None,
) -> OccupancyDecision:
    """Escolhe a área de referência para lote regular.

    Regras consolidadas nos testes finais:
    - quando houver recuos calculados, comparar TO x recuos;
    - se a área pretendida for informada, ela só pode ser adotada se ficar dentro
      da TO e do envelope de recuos existente;
    - o item de permeabilidade deve usar a mesma área adotada aqui.
    """
    to = to_float(area_to)
    recuos = to_float(area_recuos)
    pretendida_raw = to_float(area_pretendida)
    pretendida = pretendida_raw if pretendida_raw is not None and pretendida_raw > 0 else None

    bases = [v for v in (to, recuos) if v is not None]
    limite_sem_pretendida = min(bases) if bases else None

    area_adotada = limite_sem_pretendida
    if pretendida is not None:
        candidates = [pretendida]
        if to is not None:
            candidates.append(to)
        if recuos is not None:
            candidates.append(recuos)
        area_adotada = min(candidates) if candidates else pretendida

    return OccupancyDecision(
        area_to=to,
        area_recuos=recuos,
        area_pretendida=pretendida,
        area_adotada=area_adotada,
        recuos_mais_restritivos=(to is not None and recuos is not None and recuos < to),
        to_mais_restritiva=(to is not None and recuos is not None and to <= recuos),
        area_pretendida_acima_to=(pretendida is not None and to is not None and pretendida > to),
        area_pretendida_acima_recuos=(pretendida is not None and recuos is not None and pretendida > recuos),
    )
