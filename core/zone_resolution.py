from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class ZoneResolution:
    zone_sigla_raw: str
    subzone_raw: str
    zone_sigla_db: str
    subzone_code_db: str
    display_label: str
    zone_label_raw: str = ""

    def as_dict(self) -> Dict[str, str]:
        return asdict(self)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _norm(value: Any) -> str:
    text = _clean(value).upper()
    text = text.replace("–", "-")
    text = re.sub(r"\s+", " ", text)
    return text


def _extract_number(text: str, prefix: str) -> Optional[str]:
    m = re.search(rf"\b{re.escape(prefix)}\s*[-_/ ]?\s*(\d+)\b", text)
    return m.group(1) if m else None


def _extract_tag(texts: Sequence[str], prefix: str) -> Optional[str]:
    for text in texts:
        n = _extract_number(text, prefix)
        if n:
            if prefix == "ZEIP":
                return f"ZEIP_{n}"
            if prefix in {"ZEIS", "ZPP"}:
                return f"{prefix} {n}"
            if prefix in {"ZEPE", "ZEIA"}:
                return f"{prefix}{n}"
    return None


def _looks_like_app(*texts: str) -> bool:
    merged = " | ".join(_norm(t) for t in texts if t)
    return "APP" in merged or "PRESERVACAO PERMANENTE" in merged


def resolve_zone_context(
    *,
    zone_sigla: Any = None,
    subzone: Any = None,
    zone_label: Any = None,
) -> ZoneResolution:
    raw_zone = _clean(zone_sigla)
    raw_sub = _clean(subzone)
    raw_label = _clean(zone_label)

    zone_n = _norm(raw_zone)
    sub_n = _norm(raw_sub)
    label_n = _norm(raw_label)
    texts = [zone_n, sub_n, label_n]

    zone_db = zone_n or sub_n or ""
    sub_db = "PADRAO"
    display = raw_sub or raw_zone or raw_label or "—"

    if zone_n == "ZEIP":
        sector = _extract_tag(texts, "ZEIP")
        zone_db = "ZEIP"
        sub_db = sector or "PADRAO"
        display = (sector or "ZEIP").replace("_", " ")
    elif zone_n == "ZEIS" or zone_n.startswith("ZEIS "):
        specific = _extract_tag(texts, "ZEIS")
        zone_db = specific or (zone_n if zone_n.startswith("ZEIS ") else "ZEIS")
        sub_db = "PADRAO"
        display = specific or zone_db
    elif zone_n == "ZPP" or zone_n.startswith("ZPP "):
        specific = _extract_tag(texts, "ZPP")
        zone_db = specific or (zone_n if zone_n.startswith("ZPP ") else "ZPP")
        sub_db = "PADRAO"
        display = specific or zone_db
    elif zone_n == "ZEPE" or zone_n.startswith("ZEPE"):
        specific = _extract_tag(texts, "ZEPE")
        zone_db = specific or zone_n
        sub_db = "PADRAO"
        display = zone_db.replace("ZEPE", "ZEPE ") if zone_db.startswith("ZEPE") and zone_db != "ZEPE" else zone_db
    elif zone_n == "ZEIA" or zone_n.startswith("ZEIA"):
        specific = _extract_tag(texts, "ZEIA")
        if specific:
            zone_db = specific
        elif _looks_like_app(raw_zone, raw_sub, raw_label):
            zone_db = "ZEIA-APP"
        else:
            zone_db = zone_n or "ZEIA"
        sub_db = "PADRAO"
        display = zone_db.replace("ZEIA", "ZEIA ", 1) if zone_db.startswith("ZEIA") and zone_db not in {"ZEIA", "ZEIA-APP"} else zone_db
    else:
        # zonas sem subzona: usa a própria sigla como chave
        zone_db = zone_n or sub_n
        if sub_n and sub_n not in {zone_n, "PADRAO"}:
            # preserva subzona específica não conhecida para uso futuro, mas sem contaminar a regra padrão
            sub_db = sub_n
        display = raw_zone or raw_sub or raw_label or zone_db

    display = display.replace("_", " ").strip()
    if display == "":
        display = zone_db or "—"

    return ZoneResolution(
        zone_sigla_raw=raw_zone,
        subzone_raw=raw_sub,
        zone_sigla_db=zone_db,
        subzone_code_db=sub_db,
        display_label=display,
        zone_label_raw=raw_label,
    )


def resolve_zone_from_feature_properties(props: Dict[str, Any]) -> ZoneResolution:
    return resolve_zone_context(
        zone_sigla=props.get("sigla") or props.get("SIGLA") or props.get("name") or props.get("zona"),
        subzone=props.get("subzona") or props.get("SUBZONA") or props.get("subzone") or props.get("subzone_code"),
        zone_label=props.get("zona_sigla") or props.get("ZONA_SIGLA") or props.get("zona") or props.get("description"),
    )


def _zone_variants(zone_sigla_db: str) -> List[str]:
    zone = _norm(zone_sigla_db)
    out = [zone]
    # ZEPE can be stored either as ZEPE1 or ZEPE 1
    if zone.startswith("ZEPE") and len(zone) > 4 and zone[4:].isdigit():
        out.append(f"ZEPE {zone[4:]}")
    if zone.startswith("ZEPE "):
        out.append(zone.replace("ZEPE ", "ZEPE", 1))
    # ZEIA can be stored either as ZEIA1 or ZEIA 1
    if zone.startswith("ZEIA") and len(zone) > 4 and zone[4:].isdigit():
        out.append(f"ZEIA {zone[4:]}")
    if zone.startswith("ZEIA "):
        out.append(zone.replace("ZEIA ", "ZEIA", 1))
    # ZPP may exist as ZPP1/ZPP2/ZPP3 or ZPP 1/ZPP 2/ZPP 3
    if zone.startswith("ZPP") and len(zone) > 3 and zone[3:].isdigit():
        out.append(f"ZPP {zone[3:]}")
    if zone.startswith("ZPP "):
        out.append(zone.replace("ZPP ", "ZPP", 1))
    # ZEIS may also vary between ZEIS1 and ZEIS 1 in some cadastros
    if zone.startswith("ZEIS") and len(zone) > 4 and zone[4:].isdigit():
        out.append(f"ZEIS {zone[4:]}")
    if zone.startswith("ZEIS "):
        out.append(zone.replace("ZEIS ", "ZEIS", 1))
    if zone == "ZEIA-APP":
        out.append("ZEIA/APP")
    if zone == "ZEIA/APP":
        out.append("ZEIA-APP")
    seen = set()
    ordered: List[str] = []
    for item in out:
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def build_lookup_candidates(zone_sigla: Any, subzone_code: Any = "PADRAO", zone_label: Any = None) -> List[Tuple[str, str]]:
    res = resolve_zone_context(zone_sigla=zone_sigla, subzone=subzone_code, zone_label=zone_label)
    sub_candidates = [res.subzone_code_db]
    if res.subzone_code_db != "PADRAO":
        sub_candidates.append("PADRAO")
    zone_candidates = _zone_variants(res.zone_sigla_db)

    pairs: List[Tuple[str, str]] = []
    seen = set()
    for z in zone_candidates:
        for s in sub_candidates:
            key = (z, s)
            if key not in seen:
                seen.add(key)
                pairs.append(key)
    return pairs
