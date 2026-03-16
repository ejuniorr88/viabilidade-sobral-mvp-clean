from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict, Optional

try:
    from supabase import create_client  # supabase-py
except Exception:  # pragma: no cover
    create_client = None  # type: ignore


def _require_env(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise RuntimeError(f"Variável de ambiente ausente: {name}")
    return v


def get_supabase():
    """Cria client do Supabase usando SUPABASE_URL e SUPABASE_ANON_KEY."""
    if create_client is None:
        raise RuntimeError("Pacote 'supabase' não está instalado. Adicione: supabase==2.28.0")
    url = _require_env("SUPABASE_URL")
    key = _require_env("SUPABASE_ANON_KEY")
    return create_client(url, key)


def pick_value(obj: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    for k in keys:
        if k in obj and obj[k] is not None and obj[k] != "":
            return obj[k]
    return default


def pick_rule(rule: Any, *keys: str, default: Any = None) -> Any:
    if isinstance(rule, list):
        rule = rule[0] if rule else {}
    if not isinstance(rule, dict):
        return default
    return pick_value(rule, *keys, default=default)


def _to_float(v: Any) -> Optional[float]:
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        return float(v)
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(v)  # Decimal etc.
    except Exception:
        return None




def _zone_sigla_candidates(zone_sigla: str) -> list[str]:
    z = str(zone_sigla or "").strip()
    if not z:
        return []
    out = [z]
    up = z.upper()

    def _add(v: str):
        if v and v not in out:
            out.append(v)

    for base in ("ZEPE", "ZEIA", "ZEIS", "ZPP"):
        m = __import__("re").search(rf"{base}\s*-?\s*([123])$", up)
        if m:
            n = m.group(1)
            _add(f"{base}{n}")
            _add(f"{base} {n}")
    return out

def normalize_rule(rule: Dict[str, Any]) -> Dict[str, Any]:
    """Garante to_max_pct e tp_min_pct em % (0..100), mesmo que só exista fração (0..1)."""
    if not isinstance(rule, dict):
        return {}
    r = dict(rule)

    to_pct = _to_float(r.get("to_max_pct"))
    if to_pct is None:
        to_frac = _to_float(r.get("to_max"))
        to_pct = (to_frac * 100.0) if to_frac is not None else None
    if to_pct is not None:
        r["to_max_pct"] = float(to_pct)

    tp_pct = _to_float(r.get("tp_min_pct"))
    if tp_pct is None:
        tp_frac = _to_float(r.get("tp_min"))
        tp_pct = (tp_frac * 100.0) if tp_frac is not None else None
    if tp_pct is not None:
        r["tp_min_pct"] = float(tp_pct)

    ia_max = _to_float(r.get("ia_max"))
    if ia_max is not None:
        r["ia_max"] = float(ia_max)

    for k in ["recuo_frontal_m","recuo_lateral_m","recuo_fundos_m","gabarito_m",
              "area_min_lote_m2","testada_min_meio_m","testada_min_esquina_m",
              "ia_min","to_subsolo_max","to_sub_max","area_max_lote_m2","testada_max_m"]:
        if k in r:
            fv = _to_float(r.get(k))
            if fv is not None:
                r[k] = float(fv)

    if "gabarito_pav" in r and r["gabarito_pav"] is not None:
        try:
            r["gabarito_pav"] = int(r["gabarito_pav"])
        except Exception:
            pass

    return r


@lru_cache(maxsize=256)
def fetch_rule(zone_sigla: str, use_type_code: str, subzone_code: str = "PADRAO") -> Optional[Dict[str, Any]]:
    """Busca regra em zone_rules por (zone_sigla,use_type_code,subzone_code='PADRAO')."""
    sb = get_supabase()
    q = (
        sb.table("zone_rules")
        .select("*")
        .in_("zone_sigla", _zone_sigla_candidates(zone_sigla) or [zone_sigla])
        .eq("use_type_code", use_type_code)
        .eq("subzone_code", subzone_code)
        .limit(1)
    )
    res = q.execute()
    data = getattr(res, "data", None)
    if not data:
        # compat: bancos sem subzone_code
        q2 = (
            sb.table("zone_rules")
            .select("*")
            .in_("zone_sigla", _zone_sigla_candidates(zone_sigla) or [zone_sigla])
            .eq("use_type_code", use_type_code)
            .limit(1)
        )
        res2 = q2.execute()
        data2 = getattr(res2, "data", None)
        if not data2:
            return None
        return normalize_rule(data2[0])
    return normalize_rule(data[0])
