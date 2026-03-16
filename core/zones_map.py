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
    sigla_raw: str
    subzona_raw: Optional[str]
    zone_display: str
    zone_lookup: str
    subzone_code: str
    geom_prep: Any  # PreparedGeometry


def _clean_text(v: Any) -> str:
    return str(v or "").strip()


def _norm_spaces(v: str) -> str:
    return re.sub(r"\s+", " ", v).strip()


def _normalize_zone_fields(sigla_raw: Any, subzona_raw: Any) -> Dict[str, str]:
    sigla = _norm_spaces(_clean_text(sigla_raw)).upper()
    sub = _norm_spaces(_clean_text(subzona_raw)).upper()

    zone_display = sigla or "—"
    zone_lookup = sigla or "—"
    subzone_code = "PADRAO"

    # ZEIP: zona principal fixa + setor no subzone_code
    m_zeip = re.search(r"ZEIP\D*([1-9])", sub)
    if sigla == "ZEIP" and m_zeip:
        zone_display = "ZEIP"
        zone_lookup = "ZEIP"
        subzone_code = f"ZEIP_{m_zeip.group(1)}"
        return {
            "zone_display": zone_display,
            "zone_lookup": zone_lookup,
            "subzone_code": subzone_code,
        }

    # ZEIS / ZPP: no banco atual tende a usar espaço no zone_sigla (ex.: ZEIS 1)
    for base in ("ZEIS", "ZPP"):
        m = re.search(rf"{base}\D*([123])", sub)
        if sigla == base and m:
            zone_display = f"{base} {m.group(1)}"
            zone_lookup = zone_display
            return {
                "zone_display": zone_display,
                "zone_lookup": zone_lookup,
                "subzone_code": subzone_code,
            }

    # ZEPE / ZEIA: no banco atual os exemplos vieram sem espaço (ZEPE1, ZEIA1)
    for base in ("ZEPE", "ZEIA"):
        m = re.search(rf"{base}\D*([123])", sub)
        if sigla == base and m:
            zone_display = f"{base} {m.group(1)}"
            zone_lookup = f"{base}{m.group(1)}"
            return {
                "zone_display": zone_display,
                "zone_lookup": zone_lookup,
                "subzone_code": subzone_code,
            }

    # ZEIA genérica no arquivo corresponde aos trechos ZEIA/APP
    if sigla == "ZEIA" and sub == "ZEIA":
        zone_display = "ZEIA-APP"
        zone_lookup = "ZEIA-APP"
        return {
            "zone_display": zone_display,
            "zone_lookup": zone_lookup,
            "subzone_code": subzone_code,
        }

    # Zonas simples (ZCR, ZOP, ZAP, ZAM...)
    if sigla:
        zone_display = sigla
        zone_lookup = sigla

    return {
        "zone_display": zone_display,
        "zone_lookup": zone_lookup,
        "subzone_code": subzone_code,
    }


def load_zones(zone_file: Path) -> List[ZoneFeature]:
    obj = json.loads(zone_file.read_text(encoding="utf-8"))

    feats = obj.get("features") if isinstance(obj, dict) else None
    if not feats:
        raise RuntimeError("zoneamento_light.json inválido: não achei 'features'.")

    out: List[ZoneFeature] = []
    for f in feats:
        props = f.get("properties") or {}
        sigla_raw = props.get("sigla") or props.get("SIGLA") or props.get("zona") or props.get("zona_sigla")
        subzona_raw = props.get("subzona") or props.get("SUBZONA")
        if not sigla_raw:
            continue
        geom = f.get("geometry")
        if not geom:
            continue
        norm = _normalize_zone_fields(sigla_raw, subzona_raw)
        out.append(
            ZoneFeature(
                sigla_raw=_clean_text(sigla_raw),
                subzona_raw=_clean_text(subzona_raw) or None,
                zone_display=norm["zone_display"],
                zone_lookup=norm["zone_lookup"],
                subzone_code=norm["subzone_code"],
                geom_prep=prep(shape(geom)),
            )
        )

    if not out:
        raise RuntimeError("Nenhuma zona encontrada no GeoJSON.")

    return out


def zone_info_from_latlon(zones: List[ZoneFeature], lat: float, lon: float) -> Optional[Dict[str, str]]:
    p = Point(float(lon), float(lat))
    for z in zones:
        if z.geom_prep.contains(p):
            return {
                "sigla_raw": z.sigla_raw,
                "subzona_raw": z.subzona_raw or "",
                "zone_display": z.zone_display,
                "zone_lookup": z.zone_lookup,
                "subzone_code": z.subzone_code,
            }
    return None


def zone_from_latlon(zones: List[ZoneFeature], lat: float, lon: float) -> Optional[str]:
    info = zone_info_from_latlon(zones, lat, lon)
    return info["zone_display"] if info else None
