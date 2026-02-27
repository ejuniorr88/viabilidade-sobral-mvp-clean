from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .supabase_client import get_supabase


@dataclass(frozen=True)
class ZoneRule:
    zone_sigla: str
    use_type_code: str
    to_max_pct: float
    tp_min_pct: float
    ia_max: float
    recuo_frontal_m: float
    recuo_lateral_m: float
    recuo_fundos_m: float
    def get(self, key, default=None):
    return getattr(self, key, default)


def get_zone_rule(zone_sigla: str, use_type_code: str) -> Optional[ZoneRule]:
    """Fonte única: tabela public.zone_rules (Supabase).

    Chave lógica: (zone_sigla, use_type_code)
    Colunas esperadas (mínimo):
      - zone_sigla
      - use_type_code
      - to_max_pct
      - tp_min_pct
      - ia_max
      - recuo_frontal_m
      - recuo_lateral_m
      - recuo_fundos_m

    Sem fallback fixo: retorna None se não existir.
    """

    sb = get_supabase()

    resp = (
        sb.table("zone_rules")
        .select(
            "zone_sigla,use_type_code,to_max_pct,tp_min_pct,ia_max,recuo_frontal_m,recuo_lateral_m,recuo_fundos_m"
        )
        .eq("zone_sigla", zone_sigla)
        .eq("use_type_code", use_type_code)
        .limit(1)
        .execute()
    )

    data = getattr(resp, "data", None) or []
    if not data:
        return None

    row: Dict[str, Any] = data[0]

    def _f(k: str) -> float:
        v = row.get(k)
        if v is None:
            raise RuntimeError(f"Campo obrigatório ausente em zone_rules: {k}")
        return float(v)

    return ZoneRule(
        zone_sigla=str(row.get("zone_sigla")),
        use_type_code=str(row.get("use_type_code")),
        to_max_pct=_f("to_max_pct"),
        tp_min_pct=_f("tp_min_pct"),
        ia_max=_f("ia_max"),
        recuo_frontal_m=_f("recuo_frontal_m"),
        recuo_lateral_m=_f("recuo_lateral_m"),
        recuo_fundos_m=_f("recuo_fundos_m"),
    )
