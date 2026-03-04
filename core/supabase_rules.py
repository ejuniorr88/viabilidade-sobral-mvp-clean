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
        raise RuntimeError(f"Variável de ambiente ausente: {name} (configure em Streamlit → Settings → Secrets)")
    return v


def get_supabase():
    """Cria client do Supabase (supabase-py) usando Secrets:
      - SUPABASE_URL
      - SUPABASE_ANON_KEY
    """
    if create_client is None:
        raise RuntimeError("Pacote 'supabase' não está instalado. Adicione em requirements.txt: supabase==2.28.0")
    url = _require_env("SUPABASE_URL")
    key = _require_env("SUPABASE_ANON_KEY")
    return create_client(url, key)


def _jsonify_value(v: Any) -> Any:
    """Converte tipos não-JSON (Decimal, datetime, etc.) para algo serializável."""
    # Decimal -> float
    try:
        import decimal
        if isinstance(v, decimal.Decimal):
            return float(v)
    except Exception:
        pass
    # bytes -> str
    if isinstance(v, (bytes, bytearray)):
        try:
            return v.decode("utf-8", errors="ignore")
        except Exception:
            return str(v)
    return v


def normalize_rule(rule: Any) -> Optional[Dict[str, Any]]:
    if rule is None:
        return None
    if isinstance(rule, list):
        rule = rule[0] if rule else None
    if rule is None:
        return None
    if not isinstance(rule, dict):
        try:
            rule = dict(rule)  # type: ignore
        except Exception:
            return None

    out: Dict[str, Any] = {}
    for k, v in rule.items():
        out[k] = _jsonify_value(v)

    # aliases úteis (mantém compat sem duplicar lógica na UI)
    # schema real: to_max / tp_min / ia_max
    if "to_max" in out and "to_max_pct" not in out:
        out["to_max_pct"] = out["to_max"]
    if "tp_min" in out and "tp_min_pct" not in out:
        out["tp_min_pct"] = out["tp_min"]

    return out


def pick_value(obj: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    for k in keys:
        if k in obj and obj[k] is not None and obj[k] != "":
            return obj[k]
    return default


def pick_rule(rule: Any, *keys: str, default: Any = None) -> Any:
    nr = normalize_rule(rule)
    if not nr:
        return default
    return pick_value(nr, *keys, default=default)


@lru_cache(maxsize=512)
def fetch_rule(zone_sigla: str, use_type_code: str) -> Optional[Dict[str, Any]]:
    """Busca a regra em public.zone_rules filtrando por zone_sigla + use_type_code.

    Observação: esta função tem cache em memória (por processo) via lru_cache.
    """
    sb = get_supabase()
    q = (
        sb.table("zone_rules")
        .select("*")
        .eq("zone_sigla", zone_sigla)
        .eq("use_type_code", use_type_code)
        .limit(1)
    )
    res = q.execute()
    data = getattr(res, "data", None) or []
    if not data:
        return None
    return normalize_rule(data[0])
