from __future__ import annotations

import os
from typing import Any, Dict, Optional

from .zone_resolution import build_lookup_candidates

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
def fetch_rule(zone_sigla: str, use_type_code: str, subzone_code: str = "PADRAO", zone_label: str = "") -> Optional[Dict[str, Any]]:
    """Busca regra usando a resolução central de zona/subzona e fallback padronizado."""
    sb = get_supabase()
    for zone, sub in build_lookup_candidates(zone_sigla=zone_sigla, subzone_code=subzone_code, zone_label=zone_label):
        q = (
            sb.table("zone_rules")
            .select("*")
            .eq("zone_sigla", zone)
            .eq("use_type_code", use_type_code)
            .eq("subzone_code", sub)
            .limit(1)
        )
        res = q.execute()
        data = getattr(res, "data", None) or []
        if data:
            return normalize_rule(data[0])

    # compat: bancos sem subzone_code ou registros antigos
    zone_candidates = []
    for zone, _ in build_lookup_candidates(zone_sigla=zone_sigla, subzone_code=subzone_code, zone_label=zone_label):
        if zone not in zone_candidates:
            zone_candidates.append(zone)
    for zone in zone_candidates:
        q2 = (
            sb.table("zone_rules")
            .select("*")
            .eq("zone_sigla", zone)
            .eq("use_type_code", use_type_code)
            .limit(1)
        )
        res2 = q2.execute()
        data2 = getattr(res2, "data", None) or []
        if data2:
            return normalize_rule(data2[0])
    return None
