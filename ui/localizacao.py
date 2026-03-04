from __future__ import annotations

from typing import Any, Dict, Optional, Callable

import streamlit as st

from core.zones_map import zone_from_latlon
from core.zeip_sectors import zeip_sector_from_latlon


def render_localizacao_section(
    *,
    calc: Dict[str, Any],
    zone_file_path: str,
    ruas_file_path: str,
    get_nearest_road_func: Callable[..., Any],
) -> None:
    """
    Wrapper compatível: preserva layout existente.
    Apenas garante que, se zona=ZEIP, calc['subzone_code'] seja preenchido (ZEIP_1..ZEIP_9).
    """
    st.header("3) Localização (zona + via)")

    lat = calc.get("lat")
    lon = calc.get("lon")
    use_type_code = calc.get("use_type_code", "RES_UNI")

    st.text_input("use_type_code", value=use_type_code, disabled=False, key="use_type_code_input")
    calc["use_type_code"] = st.session_state.get("use_type_code_input", use_type_code)

    if lat is None or lon is None:
        st.info("Selecione um ponto no mapa e clique em Calcular viabilidade.")
        return

    zone_sigla = zone_from_latlon(lat, lon, zone_file_path=zone_file_path)
    calc["zone"] = zone_sigla
    calc["zone_sigla"] = zone_sigla

    # ZEIP sector
    subzone_code = "PADRAO"
    if zone_sigla == "ZEIP":
        try:
            subzone_code = zeip_sector_from_latlon(lat, lon) or "PADRAO"
        except Exception:
            subzone_code = "PADRAO"
    calc["subzone_code"] = subzone_code

    # nearest road (delegado ao helper já existente)
    try:
        road = get_nearest_road_func(lat=lat, lon=lon, radius_m=calc.get("radius_m", 100), ruas_file_path=ruas_file_path)
    except TypeError:
        road = get_nearest_road_func(lat, lon, calc.get("radius_m", 100), ruas_file_path)

    if isinstance(road, dict):
        calc["via_nome"] = road.get("name") or road.get("nome") or road.get("via_nome")
        calc["via_tipo"] = road.get("tipo") or road.get("type") or road.get("via_tipo")
        calc["via_dist_m"] = road.get("dist_m") or road.get("distance_m") or road.get("via_dist_m")
    else:
        calc["via_nome"] = None
        calc["via_tipo"] = None
        calc["via_dist_m"] = None

    cols = st.columns(3)
    cols[0].markdown(f"**Zona**\n\n{calc.get('zone') or '—'}")
    cols[1].markdown(f"**Rua / Logradouro**\n\n{calc.get('via_nome') or '—'}")
    cols[2].markdown(f"**Tipo de via**\n\n{calc.get('via_tipo') or '—'}")

    if calc.get("zone") == "ZEIP":
        st.caption(f"Setor ZEIP: {calc.get('subzone_code','PADRAO')}")
