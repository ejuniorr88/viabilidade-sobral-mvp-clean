from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from shapely.geometry import Point, shape
from shapely.prepared import prep


@dataclass(frozen=True)
class ZoneFeature:
    zone_sigla: str
    subzone_code: str
    display_label: str
    raw_sigla: str
    raw_subzona: str
    zona_sigla_text: str
    geom: Any
    geom_prep: Any


def _clean(v: Any) -> str:
    return str(v or "").strip()


def _extract_num(text: str, prefix: str) -> Optional[str]:
    m = re.search(rf"{re.escape(prefix)}\D*([0-9]+)", text.upper())
    return m.group(1) if m else None


def _normalize_zone(props: Dict[str, Any]) -> Dict[str, str]:
    raw_sigla = _clean(props.get("sigla") or props.get("SIGLA") or props.get("zona") or props.get("ZONA"))
    raw_sub = _clean(props.get("subzona") or props.get("SUBZONA"))
    zona_sigla_text = _clean(props.get("zona_sigla") or props.get("ZONA_SIGLA"))

    sig = raw_sigla.upper()
    sub = raw_sub.upper()
    zona_sigla_upper = zona_sigla_text.upper()

    zone_sigla = sig or raw_sigla
    subzone_code = "PADRAO"
    display_label = raw_sub or raw_sigla or sig

    if sig == "ZEIP":
        n = _extract_num(sub or zona_sigla_upper, "ZEIP")
        if n:
            subzone_code = f"ZEIP_{n}"
            display_label = f"ZEIP {n}"
        zone_sigla = "ZEIP"

    elif sig == "ZEIS":
        n = _extract_num(sub or zona_sigla_upper, "ZEIS")
        if n:
            zone_sigla = f"ZEIS {n}"
            display_label = zone_sigla
        else:
            zone_sigla = "ZEIS"
            display_label = raw_sub or raw_sigla or "ZEIS"

    elif sig == "ZEPE":
        n = _extract_num(sub or zona_sigla_upper, "ZEPE")
        if n:
            zone_sigla = f"ZEPE{n}"
            display_label = f"ZEPE {n}"
        else:
            zone_sigla = "ZEPE"
            display_label = raw_sub or raw_sigla or "ZEPE"

    elif sig == "ZPP":
        n = _extract_num(sub or zona_sigla_upper, "ZPP")
        if n:
            zone_sigla = f"ZPP {n}"
            display_label = zone_sigla
        else:
            zone_sigla = "ZPP"
            display_label = raw_sub or raw_sigla or "ZPP"

    elif sig == "ZEIA":
        zeia_text = " ".join([sig, sub, zona_sigla_upper]).upper()

        if "APP" in zeia_text:
            zone_sigla = "ZEIA-APP"
            display_label = "ZEIA-APP"
        else:
            n = _extract_num(zeia_text, "ZEIA")
            if n:
                zone_sigla = f"ZEIA{n}"
                display_label = f"ZEIA {n}"
            else:
                zone_sigla = "ZEIA"
                display_label = raw_sub or raw_sigla or "ZEIA"

    else:
        zone_sigla = sig or raw_sigla
        display_label = raw_sub or raw_sigla or zone_sigla

    return {
        "zone_sigla": zone_sigla,
        "subzone_code": subzone_code,
        "display_label": display_label,
        "raw_sigla": raw_sigla,
        "raw_subzona": raw_sub,
        "zona_sigla_text": zona_sigla_text,
    }


def _zone_specificity_rank(z: ZoneFeature) -> int:
    zone = (z.zone_sigla or "").upper()
    label = (z.display_label or "").upper()
    raw_sub = (z.raw_subzona or "").upper()
    text = " ".join([zone, label, raw_sub])

    if zone.startswith("ZEIA"):
        if re.search(r"ZEIA\s*[123]", text) or zone in {"ZEIA1", "ZEIA2", "ZEIA3"}:
            return 400
        if "APP" in text or zone == "ZEIA-APP":
            return 300
        return 200

    if zone == "ZEIP" and z.subzone_code and z.subzone_code != "PADRAO":
        return 180

    if re.search(r"(ZEIS|ZPP|ZEPE)\s*[0-9]", text):
        return 170

    return 100


def _build_zone_payload(z: ZoneFeature, *, debug: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    out = {
        "zone_sigla": z.zone_sigla,
        "subzone_code": z.subzone_code,
        "display_label": z.display_label,
        "raw_sigla": z.raw_sigla,
        "raw_subzona": z.raw_subzona,
        "zona_sigla_text": z.zona_sigla_text,
        "sigla_raw": z.raw_sigla,
        "subzona_raw": z.raw_subzona,
        "zone_display": z.display_label,
        "zone_lookup": z.zone_sigla,
    }
    if debug is not None:
        out["_debug_zone_selection"] = debug
    return out


def _candidate_debug(z: ZoneFeature, *, distance: Optional[float] = None, match_mode: str = "covers") -> Dict[str, Any]:
    item = {
        "zone_sigla": z.zone_sigla,
        "subzone_code": z.subzone_code,
        "display_label": z.display_label,
        "raw_sigla": z.raw_sigla,
        "raw_subzona": z.raw_subzona,
        "zona_sigla_text": z.zona_sigla_text,
        "specificity_rank": _zone_specificity_rank(z),
        "match_mode": match_mode,
    }
    if distance is not None:
        item["distance"] = distance
    return item


def load_zones(zone_file: Path) -> List[ZoneFeature]:
    obj = json.loads(zone_file.read_text(encoding="utf-8"))

    feats = obj.get("features") if isinstance(obj, dict) else None
    if not feats:
        raise RuntimeError("zoneamento_light.json inválido: não achei 'features'.")

    out: List[ZoneFeature] = []
    for f in feats:
        props = f.get("properties") or {}
        geom = f.get("geometry")
        if not geom:
            continue
        norm = _normalize_zone(props)
        if not norm["zone_sigla"]:
            continue
        g = shape(geom)
        out.append(
            ZoneFeature(
                zone_sigla=norm["zone_sigla"],
                subzone_code=norm["subzone_code"],
                display_label=norm["display_label"],
                raw_sigla=norm["raw_sigla"],
                raw_subzona=norm["raw_subzona"],
                zona_sigla_text=norm["zona_sigla_text"],
                geom=g,
                geom_prep=prep(g),
            )
        )

    if not out:
        raise RuntimeError("Nenhuma zona encontrada no GeoJSON.")

    return out


def zone_info_from_latlon(zones: List[ZoneFeature], lat: float, lon: float) -> Optional[Dict[str, Any]]:
    p = Point(float(lon), float(lat))
    matches: List[ZoneFeature] = []

    for z in zones:
        try:
            if z.geom_prep.covers(p):
                matches.append(z)
                continue
        except Exception:
            pass

        try:
            if z.geom.covers(p):
                matches.append(z)
        except Exception:
            continue

    if matches:
        ordered = sorted(matches, key=lambda z: (_zone_specificity_rank(z), len(z.display_label or "")), reverse=True)
        best = ordered[0]
        debug = {
            "lat": float(lat),
            "lon": float(lon),
            "selection_mode": "covers",
            "covers_count": len(matches),
            "candidates": [_candidate_debug(z) for z in ordered],
            "chosen": _candidate_debug(best),
        }
        return _build_zone_payload(best, debug=debug)

    best = None
    best_dist = None
    nearest_debug: List[Dict[str, Any]] = []
    for z in zones:
        try:
            d = float(z.geom.distance(p))
        except Exception:
            continue
        nearest_debug.append(_candidate_debug(z, distance=d, match_mode="nearest"))
        if best_dist is None or d < best_dist:
            best_dist = d
            best = z

    if best is not None and best_dist is not None and best_dist <= 0.0002:
        nearest_debug = sorted(nearest_debug, key=lambda item: (item.get("distance", 999), -item.get("specificity_rank", 0)))
        debug = {
            "lat": float(lat),
            "lon": float(lon),
            "selection_mode": "nearest_fallback",
            "nearest_threshold": 0.0002,
            "best_distance": float(best_dist),
            "candidates_preview": nearest_debug[:10],
            "chosen": _candidate_debug(best, distance=best_dist, match_mode="nearest"),
        }
        return _build_zone_payload(best, debug=debug)
    return None


def zone_from_latlon(zones: List[ZoneFeature], lat: float, lon: float) -> Optional[str]:
    info = zone_info_from_latlon(zones, lat, lon)
    return info["zone_sigla"] if info else None
