from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import streamlit as st

try:
    from core.zones_map import zone_from_latlon
except Exception:
    from core.zones_mapa import zone_from_latlon  # type: ignore

from core.streets import find_street

# ZEIP sectors
try:
    from core.zeip_sectors import zeip_sector_from_latlon
except Exception:
    zeip_sector_from_latlon = None  # type: ignore

# ZEIS sectors (NOVO)
try:
    from core.zeis_sectors import zeis_sector_from_latlon
except Exception:
    zeis_sector_from_latlon = None  # type: ignore


def _coerce_call(args, kwargs) -> Tuple[bool, Any, int]:
    if len(args) >= 3 and isinstance(args[0], (bool, int)):
        return bool(args[0]), args[1], int(args[2])
    return bool(kwargs.get("calcular", False)), kwargs.get("zones_prepared"), int(kwargs.get("radius_m", 150))


def render_localizacao_section(*args, **kwargs) -> Optional[Dict[str, Any]]:
    st.subheader("3) Localização (zona + via)")

    calcular, zones_prepared, radius_m = _coerce_call(args, kwargs)

    calc = st.session_state.calc

    # use_type_code vem do Item 2 (não editar aqui)
    use_type_code = (calc.get("use_type_code") or "RES_UNI").strip().upper()

    if calcular:
        if not getattr(st.session_state, "last_click", None):
            calc["ok"] = False
            calc["err"] = "Clique no mapa para definir o ponto."
        else:
            lat = st.session_state.last_click["lat"]
            lon = st.session_state.last_click["lon"]

            calc["lat"] = lat
            calc["lon"] = lon
            calc["use_type_code"] = use_type_code
            calc["radius_m"] = int(radius_m)

            zone = zone_from_latlon(zones_prepared, lat, lon) if zones_prepared else None

            # ZEIP: setor
            subzone_code = calc.get("subzone_code") or "PADRAO"
            if zone and str(zone).strip().upper() == "ZEIP" and zeip_sector_from_latlon:
                sec = zeip_sector_from_latlon(lat, lon)
                if sec:
                    subzone_code = sec

            # ZEIS: setor 1/2/3 (NOVO) — se o zoneamento vier como 'ZEIS'
            if zone and str(zone).strip().upper() == "ZEIS" and zeis_sector_from_latlon:
                secz = zeis_sector_from_latlon(lat, lon)
                if secz:
                    zone = secz  # vira 'ZEIS 1/2/3'

            calc["subzone_code"] = subzone_code
            calc["zone"] = zone

            # via
            street_info = find_street(lat=lat, lon=lon, radius_m=int(radius_m))
            if street_info:
                calc["via_nome"] = street_info.get("name")
                calc["via_tipo"] = street_info.get("type")
                calc["via_dist_m"] = street_info.get("dist_m")

            calc["ok"] = True

    # Exibição (sempre)
    zone = calc.get("zone") or "-"
    st.write(f"**Zona:** {zone}")
    st.write(f"**use_type_code:** {use_type_code}")

    if str(zone).strip().upper().startswith("ZEIP"):
        st.write(f"**Setor ZEIP:** {calc.get('subzone_code', 'PADRAO')}")

    return calc
