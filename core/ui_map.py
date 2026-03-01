from __future__ import annotations

import streamlit as st
from streamlit_folium import st_folium

def render_map_section(zones_gj, render_map_func, session_state_calc):
    st.subheader("1) Selecione o ponto no mapa")

    radius_m = st.number_input(
        "Raio para encontrar via (m)",
        min_value=10,
        max_value=100000,
        value=int(session_state_calc.get("radius_m") or 100),
        step=10,
    )

    if "last_click" not in st.session_state:
        st.session_state.last_click = None

    if "click_hash" not in st.session_state:
        st.session_state.click_hash = None

    last_click = st.session_state.last_click

    m = render_map_func(
        zones_gj,
        click_lat=last_click["lat"] if last_click else None,
        click_lon=last_click["lon"] if last_click else None,
    )

    out = st_folium(m, width=None, height=420)

    if out and out.get("last_clicked"):
        new_lat = float(out["last_clicked"]["lat"])
        new_lon = float(out["last_clicked"]["lng"])
        new_hash = f"{new_lat:.8f}_{new_lon:.8f}"

        if new_hash != st.session_state.click_hash:
            st.session_state.last_click = {"lat": new_lat, "lon": new_lon}
            st.session_state.click_hash = new_hash
            st.session_state.calc["ok"] = False
            st.session_state.calc["err"] = None
            st.rerun()

    if st.session_state.last_click:
        st.caption(
            f"📍 Coordenadas selecionadas: "
            f"lat {st.session_state.last_click['lat']:.6f} | "
            f"lon {st.session_state.last_click['lon']:.6f}"
        )

    calcular = st.button(
        "🔎 Calcular viabilidade",
        type="primary",
        disabled=not st.session_state.last_click,
    )

    return calcular, radius_m
