from __future__ import annotations

from typing import Any, Dict, Optional

def pick_rule(rule: Optional[Dict[str, Any]], *keys: str, default: Any = None) -> Any:
    """Pega o primeiro campo existente em `rule` dentre `keys`.

    Uso (compat):
        to_max = pick_rule(rule, "to_max_pct", "to_max", "taxa_ocupacao_max_pct")
    """
    if not rule or not isinstance(rule, dict):
        return default
    for k in keys:
        if k in rule and rule[k] is not None and rule[k] != "":
            return rule[k]
    return default
