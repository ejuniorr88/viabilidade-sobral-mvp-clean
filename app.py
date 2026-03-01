from __future__ import annotations

import uuid
import json
from pathlib import Path
from typing import Any, Optional, Dict

import streamlit as st
import folium
from streamlit_folium import st_folium

from core.zones_map import load_zones, zone_from_latlon
from core.streets import find_street
from core.zone_rules_repository import get_zone_rule

APP_TITLE = "Viabilidade"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ZONE_FILE = DATA_DIR / "zoneamento_light.json"

@st.cache_resource(show_spinner=False)
def _zones():
    with ZONE_FILE.open("r", encoding="utf-8") as f:
        gj = json.load(f)
    return {"prepared": load_zones(ZONE_FILE), "geojson": gj}

def _render_map(zones_gj, lat0=-3.689, lon0=-40.349, click_lat=None, click_lon=None):
    m = folium.Map(location=[lat0, lon0], zoom_start=12, tiles="OpenStreetMap", control_scale=True)

    folium.GeoJson(
        zones_gj,
        name="Zonas",
        style_function=lambda _: {"fillOpacity": 0.08, "weight": 1},
        tooltip=folium.GeoJsonTooltip(fields=["sigla"], aliases=["Zona"]),
    ).add_to(m)

    if click_lat and click_lon:
        folium.Marker(location=[click_lat, click_lon], tooltip="Ponto selecionado").add_to(m)

    folium.LayerControl(collapsed=True).add_to(m)
    return m

def _pick(rule: Dict[str, Any], *keys: str):
    for k in keys:
        if k in rule and rule.get(k) is not None:
            return rule.get(k)
    return None

def _fmt(v, suffix=""):
    if v is None:
        return "—"
    return f"{v}{suffix}"

def _card(title, value, suffix=""):
    st.markdown(f"""
        <div style="border:1px solid rgba(0,0,0,.08);
                    border-radius:14px;
                    padding:14px;
                    background:#fff;">
            <div style="font-size:12px; opacity:.7;">{title}</div>
            <div style="font-size:22px; font-weight:700;">{_fmt(value, suffix)}</div>
        </div>
    """, unsafe_allow_html=True)

st.set_page_config(layout="wide", page_title=APP_TITLE)
st.title(APP_TITLE)

zones = _zones()
zones_gj = zones["geojson"]

if "last_click" not in st.session_state:
    st.session_state.last_click = None
if "click_hash" not in st.session_state:
    st.session_state.click_hash = None

st.subheader("1) Selecione o ponto no mapa")

radius_m = st.number_input("Raio para encontrar via (m)", min_value=10, max_value=100000, value=100, step=10)

last_click = st.session_state.last_click

m = _render_map(
    zones_gj,
    click_lat=last_click["lat"] if last_click else None,
    click_lon=last_click["lon"] if last_click else None,
)

out = st_folium(m, height=420)

if out and out.get("last_clicked"):
    lat = float(out["last_clicked"]["lat"])
    lon = float(out["last_clicked"]["lng"])
    new_hash = f"{lat:.8f}_{lon:.8f}"
    if new_hash != st.session_state.click_hash:
        st.session_state.last_click = {"lat": lat, "lon": lon}
        st.session_state.click_hash = new_hash
        st.rerun()

if st.session_state.last_click:
    st.caption(f"📍 lat {st.session_state.last_click['lat']:.6f} | lon {st.session_state.last_click['lon']:.6f}")

calcular = st.button("🔎 Calcular viabilidade", disabled=not st.session_state.last_click)

st.divider()

st.subheader("2) Dados do lote")

lot_area = st.number_input("Área do lote (m²)", min_value=1.0, value=300.0)
built_ground = st.number_input("Área pretendida no térreo (m²)", min_value=0.0, value=0.0)

st.divider()

st.subheader("3) Localização (zona + via)")

zone = None
street = None
rule = None

if calcular and st.session_state.last_click:
    lat = st.session_state.last_click["lat"]
    lon = st.session_state.last_click["lon"]

    zone = zone_from_latlon(zones["prepared"], lat, lon)
    street = find_street(lat=lat, lon=lon, radius_m=radius_m)

    if zone:
        st.success(f"Zona detectada: {zone}")

    col1, col2, col3 = st.columns(3)
    col1.write("Zona")
    col1.write(zone or "—")
    col2.write("Rua")
    col2.write(street["name"] if street else "—")
    col3.write("Tipo de via")
    col3.write(street["type"] if street else "—")

    rule = get_zone_rule(zone, "RES_UNI") if zone else None

st.divider()

st.subheader("4) Índices Urbanísticos (Supabase)")

if rule:

    to_subsolo = _pick(rule, "to_subsolo_max", "to_sub_max")
    test_min = _pick(rule, "testada_min_meio_m", "testada_min_esquina_m")
    test_max = _pick(rule, "testada_max_m")

    to_max = _pick(rule, "to_max", "to_max_pct")
    tp_min = _pick(rule, "tp_min", "tp_min_pct")
    ia_max = _pick(rule, "ia_max")
    ia_min = _pick(rule, "ia_min")
    rec_frente = _pick(rule, "recuo_frontal_m")
    rec_fundo = _pick(rule, "recuo_fundos_m")
    rec_lateral = _pick(rule, "recuo_lateral_m")
    area_min = _pick(rule, "area_min_lote_m2")
    area_max = _pick(rule, "area_max_lote_m2")
    altura_max = _pick(rule, "gabarito_m")

    c1, c2, c3 = st.columns(3)
    _card("Zona", zone)
    _card("Taxa de Permeabilidade (TP) mínima", tp_min, "%")
    _card("Taxa de Ocupação (TO) máxima", to_max, "%")

    c4, c5, c6 = st.columns(3)
    _card("TO do Subsolo máxima", to_subsolo, "%")
    _card("Índice de Aproveitamento (IA) máximo", ia_max)
    _card("Índice de Aproveitamento (IA) mínimo", ia_min)

    c7, c8, c9 = st.columns(3)
    _card("Recuo de Frente", rec_frente, " m")
    _card("Recuo de Fundo", rec_fundo, " m")
    _card("Recuo Lateral", rec_lateral, " m")

    c10, c11, c12 = st.columns(3)
    _card("Área mínima do lote", area_min, " m²")
    _card("Testada mínima", test_min, " m")
    _card("Altura máxima (gabarito)", altura_max, " m")

    c13, c14, _ = st.columns(3)
    _card("Área máxima do lote", area_max, " m²")
    _card("Testada máxima", test_max, " m")

    with st.expander("Ver regra bruta (JSON do Supabase)"):
        st.json(rule)

