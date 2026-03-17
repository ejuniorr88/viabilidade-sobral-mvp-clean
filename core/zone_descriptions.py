from __future__ import annotations

from typing import Any, Dict, Optional

from .supabase_client import get_supabase
from .zone_resolution import build_lookup_candidates


def fetch_zone_description(zone_sigla: str, subzone_code: str = "PADRAO", zone_label: str = "") -> Optional[Dict[str, Any]]:
    """Busca a descrição da zona/subzona usando a mesma resolução central do sistema.

    Importante:
    não usar cache aqui, porque os textos podem ser inseridos/ajustados no Supabase
    e o relatório precisa refletir isso imediatamente.
    """
    sb = get_supabase()
    for zone, sub in build_lookup_candidates(
        zone_sigla=zone_sigla,
        subzone_code=subzone_code,
        zone_label=zone_label,
    ):
        res = (
            sb.table("zone_description_texts")
            .select("*")
            .eq("zone_sigla", zone)
            .eq("subzone_code", sub)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        data = getattr(res, "data", None) or []
        if data:
            return data[0]
    return None
