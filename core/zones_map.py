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
        # APP só quando houver indicação explícita de APP.
        # ZEIA1/2/3 precisam continuar específicas.
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


def _zone_specificity(z: ZoneFeature) -> tuple[int, int, float]:
    """Prefer more specific classifications when multiple features cover the same point.

    This avoids returning a broader ZEIA-APP feature just because it appears
    earlier in the GeoJSON than a more specific ZEIA1/ZEIA2/ZEIA3 polygon.
    """
    zone = (z.zone_sigla or "").upper()
    sub = (z.subzone_code or "").upper()

    family_rank = 0
    detail_rank = 0

    if zone == "ZEIP":
        family_rank = 3
        detail_rank = 2 if sub != "PADRAO" else 1
    elif zone.startswith("ZEIA"):
        family_rank = 3
        if re.fullmatch(r"ZEIA\d+", zone):
            detail_rank = 3
        elif zone == "ZEIA-APP":
            detail_rank = 2
        else:
            detail_rank = 1
    elif zone.startswith("ZEIS ") or zone.startswith("ZPP ") or re.fullmatch(r"ZEPE\d+", zone):
        family_rank = 3
        detail_rank = 2
    elif zone in {"ZEIS", "ZPP", "ZEPE"}:
        family_rank = 3
        detail_rank = 1

    area = 0.0
    try:
        area = float(z.geom.area)
    except Exception:
        area = 0.0

    return (family_rank, detail_rank, -area)


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


def zone_info_from_latlon(zones: List[ZoneFeature], lat: float, lon: float) -> Optional[Dict[str, str]]:
    p = Point(float(lon), float(lat))

    covering: List[ZoneFeature] = []
    for z in zones:
        try:
            if z.geom_prep.covers(p):
                covering.append(z)
                continue
        except Exception:
            pass
        try:
            if z.geom.covers(p):
                covering.append(z)
        except Exception:
            continue

    if covering:
        best = sorted(covering, key=_zone_specificity, reverse=True)[0]
        return {
            "zone_sigla": best.zone_sigla,
            "subzone_code": best.subzone_code,
            "display_label": best.display_label,
            "raw_sigla": best.raw_sigla,
            "raw_subzona": best.raw_subzona,
            "zona_sigla_text": best.zona_sigla_text,
            "sigla_raw": best.raw_sigla,
            "subzona_raw": best.raw_subzona,
            "zone_display": best.display_label,
            "zone_lookup": best.zone_sigla,
        }

    best = None
    best_dist = None
    for z in zones:
        try:
            d = float(z.geom.distance(p))
        except Exception:
            continue
        if best_dist is None or d < best_dist:
            best_dist = d
            best = z

    if best is not None and best_dist is not None and best_dist <= 0.0002:
        return {
            "zone_sigla": best.zone_sigla,
            "subzone_code": best.subzone_code,
            "display_label": best.display_label,
            "raw_sigla": best.raw_sigla,
            "raw_subzona": best.raw_subzona,
            "zona_sigla_text": best.zona_sigla_text,
            "sigla_raw": best.raw_sigla,
            "subzona_raw": best.raw_subzona,
            "zone_display": best.display_label,
            "zone_lookup": best.zone_sigla,
        }
    return None


def zone_from_latlon(zones: List[ZoneFeature], lat: float, lon: float) -> Optional[str]:
    info = zone_info_from_latlon(zones, lat, lon)
    return info["zone_sigla"] if info else None
