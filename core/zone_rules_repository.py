from __future__ import annotations

from typing import Any, Dict, Optional, List

from .supabase_client import get_supabase
from .zone_resolution import build_lookup_candidates


def _is_missing(v: Any) -> bool:
    """True if v is None / empty string / NaN."""
    if v is None:
        return True
    if isinstance(v, str) and v.strip() == "":
        return True
    try:
        # float('nan') != float('nan')
        return isinstance(v, float) and v != v
    except Exception:
        return False


def _pct_from_maybe_fraction(v: Any) -> Optional[float]:
    """
    Convert values that might be fraction (0.6) to pct (60.0).
    If value already looks like pct (e.g. 60), keep it.
    """
    if _is_missing(v):
        return None
    try:
        x = float(v)
    except Exception:
        return None

    # Heurística segura: se <= 1.5, provavelmente é fração
    if x <= 1.5:
        return x * 100.0
    return x


def _best_row(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Pick the most complete rule row.
    Prefer:
    - subzone_code is NULL/None (regra geral) when it is more complete
    - has *_pct fields filled
    - has testada_max / to_subsolo filled, etc.
    """
    def score(r: Dict[str, Any]) -> int:
        s = 0

        # Prefer regra geral (subzone_code vazio), mas sem forçar se ela for incompleta
        if _is_missing(r.get("subzone_code")):
            s += 5

        # Campos percentuais (mais “prontos” para UI)
        if not _is_missing(r.get("to_max_pct")):
            s += 3
        if not _is_missing(r.get("tp_min_pct")):
            s += 3

        # Campos chave
        if not _is_missing(r.get("ia_max")):
            s += 2
        if not _is_missing(r.get("gabarito_m")) or not _is_missing(r.get("altura_max_m")):
            s += 1

        # Subsolo (variações)
        if (not _is_missing(r.get("to_subsolo_max"))
            or not _is_missing(r.get("to_sub_max"))
            or not _is_missing(r.get("to_subsolo_max_pct"))):
            s += 2

        # Testadas
        if not _is_missing(r.get("testada_max_m")):
            s += 2
        if (not _is_missing(r.get("testada_min_m"))
            or not _is_missing(r.get("testada_min_meio_m"))
            or not _is_missing(r.get("testada_min_esquina_m"))):
            s += 1

        return s

    rows_sorted = sorted(rows, key=score, reverse=True)
    return rows_sorted[0]


def _merge_fill_missing(base: Dict[str, Any], other: Dict[str, Any]) -> Dict[str, Any]:
    """Fill missing fields in base with non-missing values from other."""
    out = dict(base)
    for k, v in other.items():
        if _is_missing(out.get(k)) and not _is_missing(v):
            out[k] = v
    return out


def _normalize(rule: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create normalized keys used by UI:
    - to_max_pct, tp_min_pct always set when possible
    - to_subsolo_max_pct always set when possible
    - testada_min_m computed as min(meio, esquina) if missing
    """
    r = dict(rule)

    # TO / TP percent
    if _is_missing(r.get("to_max_pct")):
        r["to_max_pct"] = _pct_from_maybe_fraction(r.get("to_max"))

    if _is_missing(r.get("tp_min_pct")):
        r["tp_min_pct"] = _pct_from_maybe_fraction(r.get("tp_min"))

    # Subsolo percent
    if _is_missing(r.get("to_subsolo_max_pct")):
        # tentamos várias colunas comuns do seu dump
        sub_raw = None
        for k in ("to_subsolo_max", "to_sub_max", "to_subsolo_pct", "to_subsolo"):
            if not _is_missing(r.get(k)):
                sub_raw = r.get(k)
                break
        r["to_subsolo_max_pct"] = _pct_from_maybe_fraction(sub_raw)

    # Testada mínima: se não tiver testada_min_m, usa min(meio, esquina)
    if _is_missing(r.get("testada_min_m")):
        vals = []
        for k in ("testada_min_meio_m", "testada_min_esquina_m", "testada_minima_m"):
            if not _is_missing(r.get(k)):
                try:
                    vals.append(float(r.get(k)))
                except Exception:
                    pass
        if vals:
            r["testada_min_m"] = min(vals)

    return r


def get_zone_rule(zone_sigla: str, use_type_code: str, subzone_code: str = "PADRAO", zone_label: str = "") -> Optional[Dict[str, Any]]:
    """
    Return the best rule for (zone, use_type, subzone), filling gaps from other candidates.
    Strategy:
    - Fetch all candidates for zone+use (and subzone_code in [requested, NULL])
    - Pick the best row (most complete)
    - Merge missing fields from the others
    - Normalize pct/testada keys so UI always receives consistent fields
    """
    sb = get_supabase()

    # Busca candidatos: subzone PADRAO e também regra geral (NULL)
    q = (
        sb.table("zone_rules")
        .select("*")
        .in_("zone_sigla", [z for z,_ in build_lookup_candidates(zone_sigla=zone_sigla, subzone_code=subzone_code, zone_label=zone_label)])
        .eq("use_type_code", use_type_code)
    )

    # Se seu Supabase aceitar in_ com None:
    try:
        q = q.in_("subzone_code", [subzone_code, "PADRAO", None])
    except Exception:
        # fallback: não filtra por subzone; traz tudo e filtra em Python
        pass

    res = q.execute()
    rows = getattr(res, "data", None) or []

    # Fallback de filtro caso o in_ acima não funcione direito
    if rows:
        filtered = []
        for r in rows:
            sc = r.get("subzone_code")
            if sc == subzone_code or sc == "PADRAO" or _is_missing(sc):
                filtered.append(r)
        if filtered:
            rows = filtered

    if not rows:
        return None

    best = _best_row(rows)

    merged = dict(best)
    for r in rows:
        merged = _merge_fill_missing(merged, r)

    merged = _normalize(merged)
    return merged
