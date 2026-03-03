from __future__ import annotations

import os
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
    """
    Cria client do Supabase (supabase-py) usando:
      - SUPABASE_URL
      - SUPABASE_ANON_KEY
    """
    if create_client is None:
        raise RuntimeError(
            "Pacote 'supabase' não está instalado. Adicione em requirements.txt: supabase"
        )
    url = _require_env("SUPABASE_URL")
    key = _require_env("SUPABASE_ANON_KEY")
    return create_client(url, key)


def pick_value(obj: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    Pega o primeiro campo existente e não-nulo dentro de 'obj'.
    Ex.: pick_value(rule, "to_max_pct", "to_max", default=None)
    """
    for k in keys:
        if k in obj and obj[k] is not None:
            return obj[k]
    return default


def pick_rule(rule: Any, *keys: str, default: Any = None) -> Any:
    """
    Compat:
    - se vier lista de regras, pega a primeira
    - depois aplica pick_value
    """
    if isinstance(rule, list):
        rule = rule[0] if rule else {}
    if not isinstance(rule, dict):
        return default
    return pick_value(rule, *keys, default=default)


def fetch_rule(zone_sigla: str, use_type_code: str) -> Optional[Dict[str, Any]]:
    """
    Busca a regra da tabela `zone_rules` filtrando por:
      - zone_sigla
      - use_type_code
    Ajuste o nome da tabela/colunas aqui se o seu Supabase estiver diferente.
    """
    sb = get_supabase()

    # tenta nomes comuns de colunas
    # (se sua tabela for diferente, me diga o nome exato das colunas)
    q = (
        sb.table("zone_rules")
        .select("*")
        .eq("zone_sigla", zone_sigla)
        .eq("use_type_code", use_type_code)
        .limit(1)
    )

    res = q.execute()
    data = getattr(res, "data", None)
    if not data:
        return None
    return data[0]
