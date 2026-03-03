import os
import json
import math
import re
import pathlib
from pathlib import Path
from typing import Dict, Any

import streamlit as st
import folium
from streamlit_folium import st_folium

from shapely.geometry import shape, Point
from shapely.ops import transform
from shapely.prepared import prep
from shapely.strtree import STRtree
from pyproj import Transformer

# =============================
# Debug markers (para garantir que o deploy está lendo o app.py correto)
# =============================
st.write("APP VERSION MARKER: 2026-03-03-XYZ")
st.write("CWD:", os.getcwd())
st.write("FILES in data/:", [p.name for p in pathlib.Path("data").glob("*")])

# =============================
# Config
# =============================
st.set_page_config(layout="wide", page_title="Viabilidade")
st.title("Viabilidade")

DATA_DIR = Path("data")
ZONE_FILE = DATA_DIR / "zoneamento_light.json"
RUAS_FILE = DATA_DIR / "ruas.json"

# =============================
# Imports do projeto (robustos)
# =============================
# Zonas (alguns branches renomearam o módulo)
try:
    from core.zones_map import load_zones
except Exception:
    from core.zones_mapa import load_zones  # type: ignore

from core.streets import load_streets, find_nearest_street

# UI (mantém layout/sections como no MVP)
from ui.mapa import render_mapa_section
from ui.localizacao import render_localizacao_section
from ui.indices import render_indices_section
from ui.analise import render_analise_section
from ui.relatorio import render_relatorio_section


# =============================
# Helpers
# =============================
def _to_float(v: Any, default: float = 0.0) -> float:
    """Converte número vindo do Streamlit aceitando ',' como separador decimal."""
    if v is None:
        return default
    if isinstance(v, (int, float)):
        try:
            return float(v)
        except Exception:
            return default
    s = str(v).strip()
    if s == "":
        return default
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return default


# =============================
# Cache (CORREÇÃO DO ERRO UnserializableReturnValueError)
# - st.cache_data: SOMENTE dados serializáveis (JSON/dict/list/str/int/float)
# - st.cache_resource: objetos "vivos" / não-serializáveis (STRtree, shapely, prep, etc)
# =============================
@st.cache_data(show_spinner=False)
def _zones_geojson() -> Dict[str, Any]:
    with open(ZONE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_resource(show_spinner=False)
def _zones_prepared():
    # Retorna estruturas com shapely/STRtree/prep (não serializável)
    return load_zones(ZONE_FILE)


@st.cache_data(show_spinner=False)
def _streets_geojson() -> Dict[str, Any]:
    with open(RUAS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_resource(show_spinner=False)
def _streets_prepared():
    """Compat: em alguns branches load_streets() não recebe path."""
    try:
        return load_streets(RUAS_FILE)  # type: ignore[arg-type]
    except TypeError:
        # Implementação atual no seu repo: load_streets() usa Path("data")/"ruas.json" internamente
        return load_streets()  # type: ignore[call-arg]


# =============================
# Estado inicial
# =============================
if "selected_lat" not in st.session_state:
    st.session_state.selected_lat = None
if "selected_lon" not in st.session_state:
    st.session_state.selected_lon = None
if "zone_sigla" not in st.session_state:
    st.session_state.zone_sigla = None
if "via_nome" not in st.session_state:
    st.session_state.via_nome = None
if "via_tipo" not in st.session_state:
    st.session_state.via_tipo = None
if "via_dist_m" not in st.session_state:
    st.session_state.via_dist_m = None
if "use_type_code" not in st.session_state:
    st.session_state.use_type_code = "RES_UNI"

# (lote)
if "lot_area" not in st.session_state:
    st.session_state.lot_area = 300.0
if "lot_front" not in st.session_state:
    st.session_state.lot_front = 10.0
if "lot_depth" not in st.session_state:
    st.session_state.lot_depth = 30.0
if "area_terreo_usuario" not in st.session_state:
    st.session_state.area_terreo_usuario = 0.0


# =============================
# Carregar bases (cache)
# =============================
Z = {"geojson": _zones_geojson(), "prepared": _zones_prepared()}
R = {"geojson": _streets_geojson(), "prepared": _streets_prepared()}


# =============================
# 1) Mapa
# =============================
render_mapa_section(Z, R)

# Botão (não mexe no layout: fica logo abaixo do mapa, como no fluxo anterior)
st.button("🔎 Calcular viabilidade", key="btn_calc")


# =============================
# 2) Dados do lote
# =============================
# OBS: removi o campo "Área permeável prevista" conforme você pediu.
# A permeabilidade deve ser calculada automaticamente (área do lote - área ocupada no térreo).
with st.container():
    st.subheader("2) Dados do lote")
    c1, c2, c3 = st.columns(3)

    with c1:
        lot_area = st.number_input("Área do lote (m²)", min_value=0.0, value=float(st.session_state.lot_area), step=10.0)
    with c2:
        lot_front = st.number_input("Largura (testada) (m)", min_value=0.0, value=float(st.session_state.lot_front), step=0.5)
    with c3:
        lot_depth = st.number_input("Profundidade (m)", min_value=0.0, value=float(st.session_state.lot_depth), step=0.5)

    area_terreo_usuario = st.number_input(
        "Área pretendida no térreo (m²)",
        min_value=0.0,
        value=float(st.session_state.area_terreo_usuario),
        step=5.0,
    )

# Persistir
st.session_state.lot_area = float(lot_area)
st.session_state.lot_front = float(lot_front)
st.session_state.lot_depth = float(lot_depth)
st.session_state.area_terreo_usuario = float(area_terreo_usuario)


# =============================
# 3) Localização (zona + via)
# =============================
render_localizacao_section(Z, R)


# =============================
# 4) Índices Urbanísticos (Supabase)
# =============================
render_indices_section()


# =============================
# 5) Análise Urbanística
# =============================
render_analise_section()


# =============================
# 6) Relatório Urbanístico
# =============================
render_relatorio_section()
