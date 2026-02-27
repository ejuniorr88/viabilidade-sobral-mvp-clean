from __future__ import annotations

from typing import Any, Dict, Optional

from .supabase_client import get_supabase


class ZoneRule(dict):
    """Dict-like rule object (JSON-serializable) with attribute access.

    Why this exists:
    - Streamlit `st.json()` expects a real JSON object (dict/list). A dataclass may break the UI.
    - Older code may call `rule.get(...)` (dict-style) or `rule.to_max_pct` (attribute-style).
    This class supports both.
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(name) from e

    def __setattr__(self, name: str, value: Any) -> None:
        # keep dict + attributes in sync
        self[name] = value

    def to_dict(self) -> Dict[str, Any]:
        return dict(self)


def get_zone_rule(zone_sigla: str, use_type_code: str, subzone_code: str = "PADRAO") -> Optional[ZoneRule]:
    """Fonte única: tabela public.zone_rules (Supabase).

    IMPORTANT:
    - Seu schema atual tem UNIQUE (zone_sigla, use_type_code, subzone_code) e subzone_code NOT NULL.
    - Para regra geral, usamos subzone_code='PADRAO'.
    """
    sb = get_supabase()
    if sb is None:
        return None

    resp = (
        sb.table("zone_rules")
        .select("*")
        .eq("zone_sigla", zone_sigla)
        .eq("use_type_code", use_type_code)
        .eq("subzone_code", subzone_code)
        .limit(1)
        .execute()
    )

    data = getattr(resp, "data", None) or []
    if not data:
        # fallback: tenta achar qualquer subzona se não existir PADRAO
        resp2 = (
            sb.table("zone_rules")
            .select("*")
            .eq("zone_sigla", zone_sigla)
            .eq("use_type_code", use_type_code)
            .limit(1)
            .execute()
        )
        data2 = getattr(resp2, "data", None) or []
        if not data2:
            return None
        row = data2[0]
    else:
        row = data[0]

    if not isinstance(row, dict):
        row = dict(row)

    return ZoneRule(**row)
