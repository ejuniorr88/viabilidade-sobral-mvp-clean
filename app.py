import os
import json
import pathlib
from pathlib import Path
from typing import Any, Dict

import streamlit as st

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

# =============================
# Imports do projeto
# =============================
# Zonas (alguns branches renomearam o módulo)
try:
    from core.zones_map import load_zones
except Exception:
    from core.zones_mapa import load_zones  # type: ignore

from core.streets import load_streets

# util de "pick" (compat). Se não existir no repo, o patch cria core/supabase_rules.py
from core.supabase_rules import pick_rule

# UI
from ui.mapa import render_mapa_section
from ui.lote import render_lote_section
from ui.localizacao import render_localizacao_section
from ui.indices import render_indices_section
from ui.analise import render_analise_section
from ui.relatorio import render_relatorio_section

# =============================
# Cache
# - st.cache_data: SOMENTE dados serializáveis (JSON/dict/list/str/int/float)
# - st.cache_resource: objetos não-serializáveis (STRtree, shapely, prep, etc)
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
    # core.streets.load_streets() já usa data/ruas.json internamente (na sua base)
    return load_streets()

# =============================
# Estado inicial
# =============================
if "selected_lat" not in st.session_state:
    st.session_state.selected_lat = None
if "selected_lon" not in st.session_state:
    st.session_state.selected_lon = None

# A UI usa st.session_state.calc (dict)
if "calc" not in st.session_state or not isinstance(st.session_state.calc, dict):
    st.session_state.calc = {}

# valor default do tipo de uso
st.session_state.calc.setdefault("use_type_code", "RES_UNI")

# =============================
# Carregar bases (cache)
# =============================
zones_gj = _zones_geojson()
zones_prepared = _zones_prepared()
streets_idx = _streets_index()  # noqa: F841 (pode ser usado internamente por outros módulos via cache)

# =============================
# 1) Mapa (seleciona lat/lon e define raio)
# =============================
radius_m = render_mapa_section(zones_gj)

# Botão (mantém o fluxo)
calcular = st.button("🔎 Calcular viabilidade", key="btn_calc")

# =============================
# 2) Dados do lote
# =============================
# ui.lote.render_lote_section() retorna um dict (compat). Extraímos aqui.
lote = render_lote_section()
if not isinstance(lote, dict):
    raise ValueError("render_lote_section() deve retornar dict (lote). Atualize ui/lote.py para o padrão novo.")

lot_area = float(lote.get("lot_area") or lote.get("area_lote") or lote.get("area_m2") or 0.0)
built_ground = float(
    lote.get("built_ground")
    or lote.get("area_terreo")
    or lote.get("area_terreo_usuario")
    or lote.get("area_terreo_m2")
    or 0.0
)

# Permeável: se a UI já calcular, usa; senão calcula simples
permeable_area = lote.get("permeable_area") or lote.get("area_permeavel")
if permeable_area is None:
    permeable_area = max(0.0, lot_area - built_ground)
else:
    permeable_area = float(permeable_area)

# =============================
# 3) Localização (zona + via)
# =============================
# Localização usa zones_prepared e raio do mapa; ruas são buscadas via core.streets internamente
_ = render_localizacao_section(calcular, zones_prepared, radius_m)

# =============================
# 4) Índices Urbanísticos (Supabase)
# =============================
# ui.indices espera: calc + pick_func + card_func (card_func geralmente já existe no módulo ui.indices)
# Para compat, tentamos chamar com kwargs; se falhar, chamamos assinatura antiga.
try:
    render_indices_section(calc=st.session_state.calc, pick_func=pick_rule, card_func=getattr(render_indices_section, "card", None))
except TypeError:
    # assinatura antiga
    render_indices_section()

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
