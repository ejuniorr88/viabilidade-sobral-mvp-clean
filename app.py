import os
import json
import math
import re
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from numbers import Integral

import streamlit as st
import folium
from streamlit_folium import st_folium

from shapely.geometry import shape, Point
from shapely.ops import transform
from shapely.prepared import prep
from shapely.strtree import STRtree
from pyproj import Transformer


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
from ui.lote import render_lote_section
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


@st.cache_data(show_spinner=False)
def _zones():
    # Retorna: preparado (STRtree/prep) e geojson bruto (para map)
    with open(ZONE_FILE, "r", encoding="utf-8") as f:
        gj = json.load(f)
    return {"prepared": load_zones(ZONE_FILE), "geojson": gj}


@st.cache_data(show_spinner=False)
def _streets():
    with open(RUAS_FILE, "r", encoding="utf-8") as f:
        gj = json.load(f)
    return {"prepared": load_streets(RUAS_FILE), "geojson": gj}


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


# =============================
# Carregar bases (cache)
# =============================
Z = _zones()
R = _streets()


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
        lot_area = st.number_input("Área do lote (m²)", min_value=0.0, value=300.0, step=10.0)
    with c2:
        lot_front = st.number_input("Largura (testada) (m)", min_value=0.0, value=10.0, step=0.5)
    with c3:
        lot_depth = st.number_input("Profundidade (m)", min_value=0.0, value=30.0, step=0.5)

    area_terreo_usuario = st.number_input("Área pretendida no térreo (m²)", min_value=0.0, value=0.0, step=5.0)

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
