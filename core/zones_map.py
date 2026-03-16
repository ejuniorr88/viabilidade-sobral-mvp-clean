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
        if "APP" in zona_sigla_upper or sub == "ZEIA":
            zone_sigla = "ZEIA-APP"
            display_label = "ZEIA-APP"
        else:
            n = _extract_num(sub or zona_sigla_upper, "ZEIA")
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

    for z in zones:
        try:
            if z.geom_prep.covers(p):
                return {
                    "zone_sigla": z.zone_sigla,
                    "subzone_code": z.subzone_code,
                    "display_label": z.display_label,
                    "raw_sigla": z.raw_sigla,
                    "raw_subzona": z.raw_subzona,
                    "zona_sigla_text": z.zona_sigla_text,
                    # compatibilidade com contrato antigo
                    "sigla_raw": z.raw_sigla,
                    "subzona_raw": z.raw_subzona,
                    "zone_display": z.display_label,
                    "zone_lookup": z.zone_sigla,
                }
        except Exception:
            try:
                if z.geom.covers(p):
                    return {
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
            except Exception:
                continue

    # fallback robusto para borda/buracos pequenos: usa polígono mais próximo
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
