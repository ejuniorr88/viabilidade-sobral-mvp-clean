from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import streamlit as st

try:
    from core.zones_map import zone_from_latlon, zone_info_from_latlon
except Exception:
    from core.zones_mapa import zone_from_latlon  # type: ignore
    zone_info_from_latlon = None  # type: ignore

from core.streets import find_street


def _coerce_call(args, kwargs) -> Tuple[bool, Any, int]:
    """Compatibilidade com app.py: render_localizacao_section(calcular, zones_prepared, radius_m)."""
    if len(args) >= 3 and isinstance(args[0], (bool, int)):
        return bool(args[0]), args[1], int(args[2])
    return bool(kwargs.get("calcular", False)), kwargs.get("zones_prepared"), int(kwargs.get("radius_m", 150))


def render_localizacao_section(*args, **kwargs) -> Optional[Dict[str, Any]]:
    st.subheader("3) Localização (zona + via)")

    calcular, zones_prepared, radius_m = _coerce_call(args, kwargs)
    calc: Dict[str, Any] = st.session_state.calc

    use_type_code = (calc.get("use_type_code") or "RES_UNI").strip().upper()
    st.text_input("use_type_code", value=use_type_code, disabled=True, key="use_type_code_readonly")

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

            prev_zone = calc.get("zone")
            prev_sub = calc.get("subzone_code") or "PADRAO"

            info = None
            if zones_prepared:
                if zone_info_from_latlon is not None:
                    try:
                        info = zone_info_from_latlon(zones_prepared, lat, lon)
                    except Exception:
                        info = None
                if info is None:
                    zone = zone_from_latlon(zones_prepared, lat, lon)
                    info = {
                        "zone_sigla": zone,
                        "subzone_code": "PADRAO",
                        "display_label": zone,
                    } if zone else None

            zone_sigla = info.get("zone_sigla") if info else None
            subzone = (info.get("subzone_code") if info else None) or "PADRAO"
            display_label = (info.get("display_label") if info else None) or zone_sigla
            zone_label_raw = (info.get("zona_sigla_text") if info else None) or display_label

            street_info = find_street(lat=lat, lon=lon, radius_m=float(radius_m))

            # contrato consolidado: a UI exibe `zone`, enquanto as consultas usam zone_sigla/subzone_code
            calc["zone"] = display_label or zone_sigla
            calc["zone_sigla"] = zone_sigla
            calc["subzone_code"] = subzone
            calc["zone_display_label"] = display_label
            calc["zone_label_raw"] = zone_label_raw
            calc["zone_raw_sigla"] = info.get("raw_sigla") if info else None
            calc["zone_raw_subzona"] = info.get("raw_subzona") if info else None
            calc["zone_zona_sigla_text"] = info.get("zona_sigla_text") if info else None

            if street_info:
                dist = street_info.get("distance_m") or street_info.get("dist_m") or street_info.get("distance")
                calc["via_nome"] = street_info.get("name")
                calc["via_tipo"] = street_info.get("type")
                calc["via_dist_m"] = dist
                calc["street_name"] = street_info.get("name")
                calc["street_type"] = street_info.get("type")
                calc["street_dist"] = dist
            else:
                calc["via_nome"] = None
                calc["via_tipo"] = None
                calc["via_dist_m"] = None
                calc["street_name"] = None
                calc["street_type"] = None
                calc["street_dist"] = None

            if calc.get("zone") != prev_zone or subzone != prev_sub:
                calc.pop("rule", None)
                calc["basic"] = None
                calc["ia_utilizado"] = None
                calc["to_utilizada_pct"] = None
                calc["tp_prevista_pct"] = None

            if not calc.get("zone"):
                calc["ok"] = False
                calc["err"] = "Clique dentro de uma zona."
            else:
                calc["ok"] = True
                calc["err"] = None

    zone = calc.get("zone")
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

    if str(calc.get("subzone_code") or "PADRAO") != "PADRAO":
        st.caption(f"Subzona/Setor: {calc.get('subzone_code', 'PADRAO')}")

    dist = calc.get("via_dist_m") if calc.get("via_dist_m") is not None else calc.get("street_dist")
    if dist is not None:
        try:
            st.caption(
                f"Distância até o eixo da via: {float(dist):.1f} m (raio {float(calc.get('radius_m') or radius_m):.0f} m)."
            )
        except Exception:
            pass

    if calc.get("err"):
        st.warning(str(calc["err"]))

    return {"zone": zone, "street": via_nome, "street_type": via_tipo, "distance_m": dist} if zone else None
