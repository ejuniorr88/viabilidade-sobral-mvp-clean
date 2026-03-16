from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .supabase_client import get_supabase


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _norm_zone(value: Any) -> str:
    return _clean_text(value).upper().replace("–", "-")


def _norm_subzone(value: Any) -> str:
    return _clean_text(value).upper().replace("–", "-")


def _zone_candidates(zone_sigla: Any) -> List[str]:
    zone = _norm_zone(zone_sigla)
    if not zone:
        return []

    candidates = [zone]

    if zone.startswith("ZEPE "):
        candidates.append(zone.replace("ZEPE ", "ZEPE", 1))
    elif zone.startswith("ZEPE") and len(zone) > 4 and zone[4].isdigit():
        candidates.append(f"ZEPE {zone[4:]}")

    if zone.startswith("ZEIA "):
        candidates.append(zone.replace("ZEIA ", "ZEIA", 1))
    elif zone.startswith("ZEIA") and len(zone) > 4 and zone[4].isdigit():
        candidates.append(f"ZEIA {zone[4:]}")

    if zone == "ZEIA/APP":
        candidates.append("ZEIA-APP")
    if zone == "ZEIA-APP":
        candidates.append("ZEIA/APP")

    # remove duplicadas preservando ordem
    seen = set()
    out: List[str] = []
    for item in candidates:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _subzone_candidates(subzone_code: Any) -> List[str]:
    sub = _norm_subzone(subzone_code)
    if not sub:
        return ["PADRAO"]
    if sub == "ZEIA":
        return ["PADRAO"]
    if sub == "PADRAO":
        return ["PADRAO"]
    return [sub, "PADRAO"]


@lru_cache(maxsize=256)
def fetch_zone_description(zone_sigla: str, subzone_code: str = "PADRAO") -> Optional[Dict[str, Any]]:
    """
    Busca a descrição da zona/subzona para o relatório.

    Estratégia:
    1) tenta a combinação exata zone_sigla + subzone_code
    2) se não achar, tenta zone_sigla + PADRAO
    3) aplica pequenas normalizações (ZEPE1/ZEPE 1, ZEIA1/ZEIA 1 etc.)
    """
    zone_candidates = _zone_candidates(zone_sigla)
    sub_candidates = _subzone_candidates(subzone_code)
    if not zone_candidates:
        return None

    sb = get_supabase()
    for zone in zone_candidates:
        for sub in sub_candidates:
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
