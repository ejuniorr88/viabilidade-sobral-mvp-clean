from __future__ import annotations

import uuid
import streamlit as st
import folium
from streamlit_folium import st_folium
from pathlib import Path
import json

from core.zones_map import load_zones, zone_from_latlon
from core.streets import find_street
from core.zone_rules_repository import get_zone_rule

APP_TITLE = "Viabilidade"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ZONE_FILE = DATA_DIR / "zoneamento_light.json"


# =============================
# Helpers
# =============================

@st.cache_resource(show_spinner=False)
def _zones():
    with ZONE_FILE.open("r", encoding="utf-8") as f:
        gj = json.load(f)
    return {
        "prepared": load_zones(ZONE_FILE),
        "geojson": gj,
    }


def _render_map(zones_gj, lat0=-3.689, lon0=-40.349, click_lat=None, click_lon=None):
    m = folium.Map(
        location=[lat0, lon0],
        zoom_start=12,
        tiles="OpenStreetMap",
        control_scale=True,
    )

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


# =============================
# App
# =============================

st.set_page_config(layout="wide", page_title=APP_TITLE)
st.title(APP_TITLE)

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

zones = _zones()
zones_gj = zones["geojson"]


# =============================
# 1) Seleção no mapa (clique único real)
# =============================

st.subheader("1) Selecione o ponto no mapa")

radius_m = st.number_input(
    "Raio para encontrar via (m)",
    min_value=10,
    max_value=100000,
    value=100,
    step=10,
)

if "last_click" not in st.session_state:
    st.session_state.last_click = None

if "click_hash" not in st.session_state:
    st.session_state.click_hash = None

last_click = st.session_state.last_click

m = _render_map(
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
        st.session_state.last_click = {
            "lat": new_lat,
            "lon": new_lon,
        }
        st.session_state.click_hash = new_hash
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

st.divider()


# =============================
# 2) Localização (zona + via)
# =============================

st.subheader("2) Localização (zona + via)")

zone = None
street_info = None

if calcular and st.session_state.last_click:

    lat = st.session_state.last_click["lat"]
    lon = st.session_state.last_click["lon"]

    zone = zone_from_latlon(zones["prepared"], lat, lon)

    if zone:
        st.success(f"Zona detectada: {zone}")
    else:
        st.warning("Clique fora das zonas.")

    street_info = find_street(
        lat=lat,
        lon=lon,
        radius_m=float(radius_m),
    )

    colA, colB, colC = st.columns(3)

    with colA:
        st.write("Zona")
        st.write(zone or "—")

    with colB:
        st.write("Rua / Logradouro")
        st.write(street_info["name"] if street_info else "Via não encontrada")

    with colC:
        st.write("Tipo de via")
        st.write(street_info["type"] if street_info else "—")

    if street_info:
        st.caption(
            f"Distância até o eixo da via: "
            f"{street_info['distance_m']:.1f} m "
            f"(raio {radius_m:.0f} m)."
        )
    else:
        st.warning(f"Via não encontrada dentro de {radius_m:.0f} m.")

st.divider()


# =============================
# 3) Dados do lote
# =============================

st.subheader("3) Dados do lote")

col1, col2, col3 = st.columns(3)

with col1:
    lot_area = st.number_input("Área do lote (m²)", min_value=1.0, value=300.0, step=10.0)

with col2:
    testada = st.number_input("Largura (testada) (m)", min_value=1.0, value=10.0, step=0.5)

with col3:
    profundidade = st.number_input("Profundidade (m)", min_value=1.0, value=30.0, step=0.5)

built_ground = st.number_input("Área pretendida no térreo (m²)", min_value=0.0, value=0.0, step=5.0)

st.subheader("4) Regras (Supabase)")

use_type_code = st.text_input("use_type_code", value="RES_UNI")


if calcular and zone:

    try:
        rule = get_zone_rule(zone, use_type_code)

        if rule:

            st.success("Regra encontrada no Supabase")
            st.json(rule, expanded=False)

            st.subheader("5) Análise Urbanística")

            to_max = rule.get("to_max_pct")
            ia_max = rule.get("ia_max")
            tp_min = rule.get("tp_min_pct")

            colA, colB, colC = st.columns(3)

            with colA:
                st.metric("TO Máxima (%)", to_max if to_max else "—")

            with colB:
                st.metric("IA Máximo", ia_max if ia_max else "—")

            with colC:
                st.metric("TP Mínima (%)", tp_min if tp_min else "—")

            if to_max:
                to_utilizada = (built_ground / lot_area) * 100
                st.write(f"TO utilizada: {to_utilizada:.2f}%")
                if to_utilizada <= to_max:
                    st.success("Taxa de Ocupação dentro do permitido")
                else:
                    st.error("Taxa de Ocupação EXCEDE o permitido")

            if ia_max:
                ia_utilizado = built_ground / lot_area
                st.write(f"IA utilizado: {ia_utilizado:.2f}")
                if ia_utilizado <= ia_max:
                    st.success("Índice de Aproveitamento dentro do permitido")
                else:
                    st.error("Índice de Aproveitamento EXCEDE o permitido")

        else:
            st.warning("Nenhuma regra encontrada para (zona + uso).")

    except Exception as e:
        st.error(f"Erro ao consultar Supabase: {e}")

st.divider()
