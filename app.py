from __future__ import annotations

import os
import json
import pathlib
from pathlib import Path
from typing import Any, Dict

import streamlit as st

# =============================
# Debug markers (garantir que o deploy está lendo o app.py correto)
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

# =============================
# Imports do projeto
# =============================
# Zonas (alguns branches renomearam o módulo)
try:
    from core.zones_map import load_zones
except Exception:
    from core.zones_mapa import load_zones  # type: ignore

from core.streets import load_streets
from core.supabase_rules import fetch_rule, pick_rule  # <-- IMPORT CERTO (busca + pick)

# UI
from ui.mapa import render_mapa_section
from ui.lote import render_lote_section
from ui.localizacao import render_localizacao_section
from ui.indices import render_indices_section
from ui.analise import render_analise_section
from ui.relatorio import render_relatorio_section

# =============================
# Cache
# =============================
@st.cache_data(show_spinner=False)
def _zones_geojson() -> Dict[str, Any]:
    with open(ZONE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_resource(show_spinner=False)
def _zones_prepared():
    return load_zones(ZONE_FILE)

@st.cache_resource(show_spinner=False)
def _streets_index():
    # core.streets.load_streets() já usa data/ruas.json internamente
    return load_streets()

# =============================
# Estado inicial
# =============================
if "selected_lat" not in st.session_state:
    st.session_state.selected_lat = None
if "selected_lon" not in st.session_state:
    st.session_state.selected_lon = None

# A UI usa st.session_state.calc (dict)
if "calc" not in st.session_state:
    st.session_state.calc = {}

# default do tipo de uso
st.session_state.calc.setdefault("use_type_code", "RES_UNI")

# =============================
# Carregar bases (cache)
# =============================
zones_gj = _zones_geojson()
zones_prepared = _zones_prepared()
_ = _streets_index()  # só garante que ruas estão indexadas/cached

# =============================
# 1) Mapa (seleciona lat/lon e define raio)
# =============================
radius_m = render_mapa_section(zones_gj)

# Botão (mantém o fluxo)
calcular = st.button("🔎 Calcular viabilidade", key="btn_calc")

# =============================
# 2) Dados do lote
# =============================
lot_area, built_ground, permeable_area = render_lote_section()

# =============================
# 3) Localização (zona + via)
# =============================
# Isso deve preencher calc["zone"], calc["via_nome"], etc.
_ = render_localizacao_section(calcular, zones_prepared, radius_m)

# =============================
# “Armar” calc.ok no clique do botão
# =============================
if calcular:
    # reset básico de erros para novo cálculo
    st.session_state.calc["err"] = None
    # se a zona foi encontrada na seção 3, então ok = True
    if st.session_state.calc.get("zone"):
        st.session_state.calc["ok"] = True
    else:
        st.session_state.calc["ok"] = False
        st.session_state.calc["err"] = "Zona não definida (clique no mapa e calcule)."
        st.session_state.calc["rule"] = None

# =============================
# 4) Índices Urbanísticos (Supabase)
# =============================
# IMPORTANTE: passar get_rule_func para a Opção B funcionar
# card_func: se você já tem um card helper em algum lugar, troque aqui.
# Se não tiver, usamos um fallback simples.
def _card(title: str, value: Any, suffix: str = ""):
    v = "-" if value is None or value == "" else value
    st.metric(title, f"{v}{suffix}")

render_indices_section(
    calc=st.session_state.calc,
    card_func=_card,
    pick_func=pick_rule,
    get_rule_func=fetch_rule,
)

# =============================
# 5) Análise Urbanística
# =============================
render_analise_section(
    st.session_state.calc,
    lot_area=lot_area,
    built_ground=built_ground,
    permeable_area=permeable_area,
    pick_func=pick_rule,
)

# =============================
# 6) Relatório Urbanístico
# =============================
render_relatorio_section(st.session_state.calc)
