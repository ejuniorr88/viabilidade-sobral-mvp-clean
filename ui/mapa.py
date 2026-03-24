from __future__ import annotations

import os
from typing import Any, Dict, Optional

import folium
import streamlit as st
from streamlit_folium import st_folium

from components.google_map_component import render_google_map


def _get_map_provider() -> str:
    provider = (
        st.secrets.get("MAP_PROVIDER")
        or os.getenv("MAP_PROVIDER")
        or "folium"
    )
    return str(provider).strip().lower()


def _get_google_maps_api_key() -> str:
    return str(
        st.secrets.get("GOOGLE_MAPS_API_KEY")
        or os.getenv("GOOGLE_MAPS_API_KEY")
        or ""
    ).strip()


def _render_folium_map(zones_gj, lat0=-3.689, lon0=-40.349, click_lat=None, click_lon=None):
    m = folium.Map(
        location=[lat0, lon0],
        zoom_start=12,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    if zones_gj:
        folium.GeoJson(
            zones_gj,
            name="Zonas",
            style_function=lambda _: {"fillOpacity": 0.08, "weight": 1},
            tooltip=folium.GeoJsonTooltip(fields=["sigla"], aliases=["Zona"]),
        ).add_to(m)

    if click_lat is not None and click_lon is not None:
        folium.Marker(
            location=[click_lat, click_lon],
            tooltip="Ponto selecionado",
        ).add_to(m)

    folium.LayerControl(collapsed=True).add_to(m)
    return m


def _apply_click_update(
    new_lat: float,
    new_lon: float,
    *,
    state_key_last_click: str,
    state_key_click_hash: str,
    state_key_calc: str,
    radius_m: int,
) -> bool:
    new_hash = f"{new_lat:.8f}_{new_lon:.8f}"
    if new_hash == st.session_state.get(state_key_click_hash):
        return False

    st.session_state[state_key_last_click] = {"lat": new_lat, "lon": new_lon}
    st.session_state[state_key_click_hash] = new_hash

    calc = st.session_state.get(state_key_calc) or {}
    if isinstance(calc, dict):
        calc["ok"] = False
        calc["err"] = None
        calc["radius_m"] = int(radius_m)
        calc["zone"] = None
        calc["zone_sigla"] = None
        calc["via_nome"] = None
        calc["via_tipo"] = None
        calc["via_dist_m"] = None
        calc["street_name"] = None
        calc["street_type"] = None
        calc["street_dist"] = None
        calc["rule"] = None
        calc["basic"] = None
        calc["ia_utilizado"] = None
        calc["to_utilizada_pct"] = None
        calc["tp_prevista_pct"] = None
        calc["_click_hash"] = new_hash
        st.session_state[state_key_calc] = calc
    return True


def _render_google_map_section(
    zones_gj: Optional[Dict[str, Any]],
    *,
    click_lat: Optional[float],
    click_lon: Optional[float],
    radius_m: int,
    state_key_last_click: str,
    state_key_click_hash: str,
    state_key_calc: str,
) -> bool:
    api_key = _get_google_maps_api_key()
    if not api_key:
        st.info(
            "Mapa Google ainda sem chave configurada. O sistema voltou automaticamente para o mapa atual. "
            "Adicione GOOGLE_MAPS_API_KEY e MAP_PROVIDER=google para ativar esta fase."
        )
        return False

    result = render_google_map(
        api_key=api_key,
        center_lat=-3.689,
        center_lng=-40.349,
        zoom=12,
        click_lat=click_lat,
        click_lng=click_lon,
        radius_m=radius_m,
        zones_geojson=zones_gj,
        height=420,
        key="google_map_section_main",
    ) or {}

    if result.get("error"):
        st.warning(f"Mapa Google indisponível neste momento: {result['error']}. Voltando ao mapa atual.")
        return False

    clicked_lat = result.get("clicked_lat")
    clicked_lng = result.get("clicked_lng")
    if clicked_lat is None or clicked_lng is None:
        return True

    changed = _apply_click_update(
        float(clicked_lat),
        float(clicked_lng),
        state_key_last_click=state_key_last_click,
        state_key_click_hash=state_key_click_hash,
        state_key_calc=state_key_calc,
        radius_m=radius_m,
    )

    # Só rerun quando o ponto mudou de verdade.
    if changed:
        st.rerun()

    return True


def render_mapa_section(
    zones_gj,
    *,
    state_key_last_click: str = "last_click",
    state_key_click_hash: str = "click_hash",
    state_key_calc: str = "calc",
    default_radius_m: int = 100,
) -> int:
    st.subheader("1) Selecione o ponto no mapa")

    radius_m = st.number_input(
        "Raio para encontrar via (m)",
        min_value=10,
        max_value=100000,
        value=int((st.session_state.get(state_key_calc, {}) or {}).get("radius_m") or default_radius_m),
        step=10,
    )

    last_click = st.session_state.get(state_key_last_click)
    click_lat = last_click["lat"] if last_click else None
    click_lon = last_click["lon"] if last_click else None

    provider = _get_map_provider()
    used_google = False
    if provider == "google":
        used_google = _render_google_map_section(
            zones_gj,
            click_lat=click_lat,
            click_lon=click_lon,
            radius_m=int(radius_m),
            state_key_last_click=state_key_last_click,
            state_key_click_hash=state_key_click_hash,
            state_key_calc=state_key_calc,
        )

    if not used_google:
        m = _render_folium_map(
            zones_gj,
            click_lat=click_lat,
            click_lon=click_lon,
        )
        out = st_folium(m, width=None, height=420)
        if out and out.get("last_clicked"):
            new_lat = float(out["last_clicked"]["lat"])
            new_lon = float(out["last_clicked"]["lng"])
            changed = _apply_click_update(
                new_lat,
                new_lon,
                state_key_last_click=state_key_last_click,
                state_key_click_hash=state_key_click_hash,
                state_key_calc=state_key_calc,
                radius_m=int(radius_m),
            )
            if changed:
                st.rerun()

    if st.session_state.get(state_key_last_click):
        st.caption(
            f"📍 Coordenadas selecionadas: "
            f"lat {st.session_state[state_key_last_click]['lat']:.6f} | "
            f"lon {st.session_state[state_key_last_click]['lon']:.6f}"
        )

    return int(radius_m)
