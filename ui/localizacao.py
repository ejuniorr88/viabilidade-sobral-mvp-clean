from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import streamlit as st

try:
    from core.zones_map import zone_from_latlon
except Exception:
    from core.zones_mapa import zone_from_latlon  # type: ignore

from core.streets import find_street


def _coerce_call(args, kwargs) -> Tuple[bool, Any, int]:
    if len(args) >= 3 and isinstance(args[0], (bool, int)):
        return bool(args[0]), args[1], int(args[2])
    return bool(kwargs.get("calcular", False)), kwargs.get("zones_prepared"), int(kwargs.get("radius_m", 150))


def render_localizacao_section(*args, **kwargs) -> Optional[Dict[str, Any]]:
    st.subheader("3) Localização (zona + via)")

    calcular, zones_prepared, radius_m = _coerce_call(args, kwargs)

    use_type_code = st.text_input(
        "use_type_code",
        value=st.session_state.calc.get("use_type_code") or "RES_UNI",
        key="use_type_code_input",
    )

    calc = st.session_state.calc

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
            street_info = find_street(lat=lat, lon=lon, radius_m=float(radius_m))

            calc["zone"] = zone
            calc["zone_sigla"] = zone

            if street_info:
                calc["via_nome"] = street_info.get("name")
                calc["via_tipo"] = street_info.get("type")
                calc["via_dist_m"] = street_info.get("distance_m")
                calc["street_name"] = street_info.get("name")
                calc["street_type"] = street_info.get("type")
                calc["street_dist"] = street_info.get("distance_m")
            else:
                calc["via_nome"] = None
                calc["via_tipo"] = None
                calc["via_dist_m"] = None
                calc["street_name"] = None
                calc["street_type"] = None
                calc["street_dist"] = None

            if not zone:
                calc["ok"] = False
                calc["err"] = "Clique dentro de uma zona."
            else:
                calc["ok"] = True
                calc["err"] = None

    zone = calc.get("zone") or calc.get("zone_sigla")
    via_nome = calc.get("via_nome") or calc.get("street_name")
    via_tipo = calc.get("via_tipo") or calc.get("street_type")

    colA, colB, colC = st.columns(3)
    with colA:
        st.write("Zona")
        st.write(zone or "—")
    with colB:
        st.write("Rua / Logradouro")
        st.write(via_nome or "—")
    with colC:
        st.write("Tipo de via")
        st.write(via_tipo or "—")

    dist = calc.get("via_dist_m") if calc.get("via_dist_m") is not None else calc.get("street_dist")
    if dist is not None:
        try:
            st.caption(f"Distância até o eixo da via: {float(dist):.1f} m (raio {float(calc.get('radius_m') or radius_m):.0f} m).")
        except Exception:
            pass

    if calc.get("err"):
        st.warning(str(calc["err"]))

    return {"zone": zone, "street": via_nome, "street_type": via_tipo, "distance_m": dist} if zone else None
