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


def _get(rule, *keys):
    for k in keys:
        if k in rule and rule[k] is not None:
            return rule[k]
    return "—"


# =============================
# App
# =============================

st.set_page_config(layout="wide", page_title=APP_TITLE)
st.title(APP_TITLE)

zones = _zones()
zones_gj = zones["geojson"]


# 1) MAPA
st.header("1) Selecione o ponto no mapa")

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
    lat = float(out["last_clicked"]["lat"])
    lon = float(out["last_clicked"]["lng"])
    new_hash = f"{lat:.8f}_{lon:.8f}"

    if new_hash != st.session_state.click_hash:
        st.session_state.last_click = {"lat": lat, "lon": lon}
        st.session_state.click_hash = new_hash
        st.rerun()

if st.session_state.last_click:
    st.caption(
        f"📍 lat {st.session_state.last_click['lat']:.6f} | "
        f"lon {st.session_state.last_click['lon']:.6f}"
    )

st.divider()


# 2) DADOS DO LOTE
st.header("2) Dados do lote")

lot_area = st.number_input("Área do lote (m²)", 1.0, 1000000.0, 300.0)
built_ground = st.number_input("Área térrea (m²)", 0.0, 1000000.0, 0.0)
area_total = st.number_input("Área total construída (m²)", 0.0, 1000000.0, 0.0)

calcular = st.button("🔎 Calcular viabilidade", type="primary",
                     disabled=not st.session_state.last_click)

st.divider()


if calcular and st.session_state.last_click:

    lat = st.session_state.last_click["lat"]
    lon = st.session_state.last_click["lon"]

    # 3) LOCALIZAÇÃO
    st.header("3) Localização (zona + via)")

    zone = zone_from_latlon(zones["prepared"], lat, lon)
    street = find_street(lat=lat, lon=lon, radius_m=100)

    col1, col2, col3 = st.columns(3)
    col1.write("Zona")
    col1.write(zone or "—")
    col2.write("Rua")
    col2.write(street["name"] if street else "—")
    col3.write("Tipo de via")
    col3.write(street["type"] if street else "—")

    st.divider()

    # 4) ÍNDICES URBANÍSTICOS
    st.header("4) Índices Urbanísticos")

    use_type_code = st.text_input("use_type_code", value="RES_UNI")
    rule = get_zone_rule(zone, use_type_code) if zone else None

    if rule:

        indices = {
            "Zona": zone,
            "Taxa de Permeabilidade (%)": _get(rule, "tp_min_pct"),
            "Taxa de Ocupação (%)": _get(rule, "to_max_pct"),
            "TO Subsolo (%)": _get(rule, "to_subsolo_pct"),
            "IA Máximo": _get(rule, "ia_max"),
            "IA Mínimo": _get(rule, "ia_min"),
            "Recuo Frente (m)": _get(rule, "recuo_frontal_m", "setback_front"),
            "Recuo Fundo (m)": _get(rule, "recuo_fundo_m"),
            "Recuo Lateral (m)": _get(rule, "recuo_lateral_m"),
            "Área Mínima Lote (m²)": _get(rule, "area_min_lote"),
            "Área Máxima Lote (m²)": _get(rule, "area_max_lote"),
            "Testada Mínima (m)": _get(rule, "testada_min"),
            "Testada Máxima (m)": _get(rule, "testada_max"),
            "Altura Máxima / Gabarito (m)": _get(rule, "altura_max_m", "height_max_m"),
        }

        st.dataframe(indices.items(), use_container_width=True)

        st.divider()

        # 5) ANÁLISE
        st.header("5) Análise Urbanística")

        ia_max = rule.get("ia_max")
        to_max = rule.get("to_max_pct")
        tp_min = rule.get("tp_min_pct")

        if ia_max and area_total:
            ia_util = area_total / lot_area
            st.write(f"IA utilizado: {ia_util:.2f}")
            st.success("✔ Dentro do permitido" if ia_util <= ia_max else "✖ Excede o permitido")

        if to_max and built_ground:
            to_util = (built_ground / lot_area) * 100
            st.write(f"TO utilizada: {to_util:.2f}%")
            st.success("✔ Dentro do permitido" if to_util <= to_max else "✖ Excede o permitido")

        if tp_min:
            st.info("Informe área permeável futuramente para validar TP corretamente.")

    else:
        st.warning("Regra não encontrada.")
