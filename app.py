import os
import json
import pathlib
from pathlib import Path
from typing import Any, Dict, Callable, Optional

import streamlit as st

# =============================
# Debug markers (garante que o deploy está lendo o app.py correto)
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

# UI
from ui.mapa import render_mapa_section
from ui.lote import render_lote_section
from ui.localizacao import render_localizacao_section
from ui.indices import render_indices_section
from ui.analise import render_analise_section
from ui.relatorio import render_relatorio_section


# =============================
# Import "robusto" do pick_rule (Supabase)
# - NÃO pode derrubar o app inteiro se o módulo não existir no deploy
# =============================
PickFunc = Optional[Callable[..., Any]]
pick_rule: PickFunc = None

try:
    # caminho esperado
    from core.supabase_rules import pick_rule as _pick_rule  # type: ignore
    pick_rule = _pick_rule
except Exception:
    # fallback (caso seu projeto tenha outro nome de arquivo)
    try:
        from core.supabase_rule import pick_rule as _pick_rule  # type: ignore
        pick_rule = _pick_rule
    except Exception:
        pick_rule = None


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
    # core.streets.load_streets() já usa data/ruas.json internamente (conforme seu comentário)
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

# valor default do tipo de uso
st.session_state.calc.setdefault("use_type_code", "RES_UNI")


# =============================
# Carregar bases (cache)
# =============================
zones_gj = _zones_geojson()
zones_prepared = _zones_prepared()
_ = _streets_index()  # garante que índice de ruas está carregado


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
_ = render_localizacao_section(calcular, zones_prepared, radius_m)


# =============================
# 4) Índices Urbanísticos (Supabase)
# =============================
render_indices_section()


# =============================
# 5) Análise Urbanística
# =============================
if pick_rule is None:
    st.warning(
        "Módulo de regras do Supabase não encontrado no deploy "
        "(core/supabase_rules.py). A análise vai rodar sem buscar regras no Supabase."
    )
    # fallback: retorna None (seu render_analise_section deve lidar com isso)
    def _pick_rule_fallback(*args: Any, **kwargs: Any) -> Any:
        return None

    pick_func = _pick_rule_fallback
else:
    pick_func = pick_rule

render_analise_section(
    st.session_state.calc,
    lot_area=lot_area,
    built_ground=built_ground,
    permeable_area=permeable_area,
    pick_func=pick_func,
)


# =============================
# 6) Relatório Urbanístico
# =============================
render_relatorio_section(st.session_state.calc)
