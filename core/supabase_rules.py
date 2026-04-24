from __future__ import annotations

import os
from typing import Any, Dict, Iterable, Optional

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

    for k in [
        "recuo_frontal_m",
        "recuo_lateral_m",
        "recuo_fundos_m",
        "gabarito_m",
        "area_min_lote_m2",
        "testada_min_meio_m",
        "testada_min_esquina_m",
        "ia_min",
        "to_subsolo_max",
        "to_sub_max",
        "area_max_lote_m2",
        "testada_max_m",
    ]:
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


def _zone_variants(zone: str) -> list[str]:
    """Expande apenas variantes de escrita da mesma zona, preservando prioridade.

    Importante:
    - não transformar ZEIA1/2/3 em ZEIA genérica
    - aceitar variante com underscore para ZEIA-APP
    """
    z = (zone or "").strip()
    if not z:
        return []

    variants: list[str] = []
    def add(v: str) -> None:
        v = (v or "").strip()
        if v and v not in variants:
            variants.append(v)

    add(z)

    normalized = z.upper().replace(" ", "").replace("/", "-")
    if normalized == "ZEIA-APP":
        add("ZEIA-APP")
        add("ZEIA APP")
        add("ZEIA/APP")
        add("ZEIA_APP")
    return variants


def _lookup_candidates(zone_sigla: str, subzone_code: str = "PADRAO", zone_label: str = "") -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []
    for zone, sub in build_lookup_candidates(zone_sigla=zone_sigla, subzone_code=subzone_code, zone_label=zone_label):
        for variant in _zone_variants(zone):
            item = (variant, sub)
            if item not in candidates:
                candidates.append(item)
    return candidates


def _normalize_text(value: Any) -> str:
    return str(value or "").strip().upper()


def _normalize_subzone(value: Any) -> Optional[str]:
    text = _normalize_text(value)
    if not text or text == "NULL":
        return None
    return text


def _subzone_candidates(subzone_code: Any) -> list[Optional[str]]:
    normalized = _normalize_subzone(subzone_code)
    candidates: list[Optional[str]] = []

    def add(value: Optional[str]) -> None:
        if value not in candidates:
            candidates.append(value)

    if normalized and normalized != "PADRAO":
        add(normalized)
    add("PADRAO")
    add(None)
    return candidates


def _resolved_subzone_candidates(zone_sigla: str, subzone_code: Any, zone_label: str = "") -> list[Optional[str]]:
    """Resolve subzone priority using the same normalization path as zone resolution.

    This avoids choosing PADRAO when the input subzone is a human-facing variant
    such as ``ZEIP 3`` while the database stores ``ZEIP_3``.
    """
    candidates: list[Optional[str]] = []

    def add(value: Optional[str]) -> None:
        if value not in candidates:
            candidates.append(value)

    for _zone, sub in _lookup_candidates(zone_sigla=zone_sigla, subzone_code=subzone_code, zone_label=zone_label):
        normalized = _normalize_subzone(sub)
        if normalized is not None:
            add(normalized)

    for value in _subzone_candidates(subzone_code):
        add(value)

    return candidates


def _pick_best_row(
    rows: Iterable[Dict[str, Any]],
    *,
    zone_sigla: str,
    requested_subzone: Any,
    zone_label: str = "",
) -> Optional[Dict[str, Any]]:
    subzone_order = {
        value: idx
        for idx, value in enumerate(
            _resolved_subzone_candidates(zone_sigla=zone_sigla, subzone_code=requested_subzone, zone_label=zone_label)
        )
    }

    best: Optional[Dict[str, Any]] = None
    best_score: Optional[tuple[int, int]] = None
    for row in rows:
        row_subzone = _normalize_subzone(row.get("subzone_code"))
        priority = subzone_order.get(row_subzone)
        if priority is None:
            continue
        completeness = sum(1 for value in row.values() if value not in (None, ""))
        score = (priority, -completeness)
        if best is None or score < best_score:
            best = row
            best_score = score
    return best


def _use_type_candidates(use_type_code: str) -> list[str]:
    """Return additive lookup candidates for residential multifamiliar variants.

    The database may have parameters saved under only one multifamiliar subtype
    even though the UI offers R2.1, R2.2 and R3 separately. For parameter lookup
    they share the same urban indices, so when the requested multifamiliar code
    has no exact row we must try the sibling multifamiliar codes before failing.
    """
    code = str(use_type_code or "").strip().upper()
    if not code:
        return []

    variants = [code]
    if code.startswith("RES_MULTI_") or code == "RES_MULTI":
        for alt in ("RES_MULTI_R21", "RES_MULTI_R22", "RES_MULTI_R3", "RES_MULTI"):
            if alt not in variants:
                variants.append(alt)
    return variants

def fetch_rule(zone_sigla: str, use_type_code: str, subzone_code: str = "PADRAO", zone_label: str = "") -> Optional[Dict[str, Any]]:
    """Busca regra usando resolução central de zona/subzona e fallback consistente.

    Ordem de prioridade:
    1) mesma zona + subzona exata (já normalizada pela resolução central)
    2) mesma zona + PADRAO
    3) mesma zona + subzona vazia/NULL

    Para multifamiliar, se o subtipo pedido não existir, tenta os demais subtipos
    irmãos sem ultrapassar a prioridade de subzona.
    """
    sb = get_supabase()
    use_candidates = _use_type_candidates(use_type_code)
    requested_code = str(use_type_code or "").strip().upper()

    # Caminho principal: mantém a prioridade exata das combinações resolvidas
    # por zone_resolution/build_lookup_candidates.
    for requested_use in use_candidates:
        for zone, sub in _lookup_candidates(zone_sigla=zone_sigla, subzone_code=subzone_code, zone_label=zone_label):
            q = (
                sb.table("zone_rules")
                .select("*")
                .eq("zone_sigla", zone)
                .eq("use_type_code", requested_use)
                .eq("subzone_code", sub)
                .limit(1)
            )
            res = q.execute()
            data = getattr(res, "data", None) or []
            if data:
                rule = normalize_rule(data[0])
                rule.setdefault("requested_use_type_code", requested_code)
                rule.setdefault("resolved_use_type_code", requested_use)
                return rule

    # Compatibilidade com bancos antigos/linhas sem subzone_code: busca todas as
    # linhas da zona+uso e escolhe a melhor pela mesma prioridade de subzona já
    # normalizada (por exemplo: ZEIP 3 -> ZEIP_3 antes de PADRAO).
    zone_candidates: list[str] = []
    for zone, _ in _lookup_candidates(zone_sigla=zone_sigla, subzone_code=subzone_code, zone_label=zone_label):
        if zone not in zone_candidates:
            zone_candidates.append(zone)

    for requested_use in use_candidates:
        for zone in zone_candidates:
            q2 = (
                sb.table("zone_rules")
                .select("*")
                .eq("zone_sigla", zone)
                .eq("use_type_code", requested_use)
            )
            res2 = q2.execute()
            rows = getattr(res2, "data", None) or []
            best = _pick_best_row(rows, zone_sigla=zone, requested_subzone=subzone_code, zone_label=zone_label)
            if best:
                rule = normalize_rule(best)
                rule.setdefault("requested_use_type_code", requested_code)
                rule.setdefault("resolved_use_type_code", requested_use)
                return rule

    return None
