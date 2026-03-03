import os
import json
import pathlib
from pathlib import Path
from typing import Any, Dict

import streamlit as st

# =============================
# Debug markers (remova depois)
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
try:
    from core.zones_map import load_zones
except Exception:
    from core.zones_mapa import load_zones  # type: ignore

from core.streets import load_streets

# SUPABASE (Opção B)
from core.supabase_rules import fetch_rule, pick_rule, pick_value

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
    # core.streets.load_streets() pode usar data/ruas.json internamente
    return load_streets()


# =============================
# Estado inicial
# =============================
if "selected_lat" not in st.session_state:
    st.session_state.selected_lat = None
if "selected_lon" not in st.session_state:
    st.session_state.selected_lon = None

# UI usa st.session_state.calc
if "calc" not in st.session_state or not isinstance(st.session_state.calc, dict):
    st.session_state.calc = {}

st.session_state.calc.setdefault("use_type_code", "RES_UNI")


# =============================
# Carregar bases
# =============================
zones_gj = _zones_geojson()
zones_prepared = _zones_prepared()
_ = _streets_index()  # garante index/cache (se seu core.streets precisar)


# =============================
# 1) Mapa
# =============================
radius_m = render_mapa_section(zones_gj)

calcular = st.button("🔎 Calcular viabilidade", key="btn_calc")


# =============================
# 2) Dados do lote
# =============================
lote = render_lote_section()  # <- seu ui/lote.py retorna dict

# Normaliza campos esperados
lot_area = float(lote.get("lot_area_m2") or 0.0)
built_ground = float(lote.get("built_ground_m2") or 0.0)
permeable_area = float(lote.get("permeable_area_m2") or 0.0)


# =============================
# 3) Localização (zona + via)
# =============================
# Esperado: essa função preenche zone_sigla/via_nome etc dentro de st.session_state.calc
_ = render_localizacao_section(calcular, zones_prepared, radius_m)


# =============================
# 4) Supabase (Opção B): buscar regra e salvar em calc
# =============================
if calcular:
    zone_sigla = st.session_state.calc.get("zone_sigla") or st.session_state.calc.get("zone")
    use_type_code = st.session_state.calc.get("use_type_code", "RES_UNI")

    st.session_state.calc["ok"] = False
    st.session_state.calc["err"] = None
    st.session_state.calc["rule"] = None

    if not zone_sigla:
        st.session_state.calc["err"] = "Zona não definida (clique no mapa e calcule)."
    else:
        try:
            rule = fetch_rule(str(zone_sigla), str(use_type_code))
            st.session_state.calc["rule"] = rule
            st.session_state.calc["zone"] = str(zone_sigla)
            st.session_state.calc["ok"] = True
            if rule is None:
                st.session_state.calc["err"] = "Nenhuma regra encontrada no Supabase para (zona + uso)."
        except Exception as e:
            st.session_state.calc["err"] = f"Erro ao consultar Supabase: {e!s}"


# =============================
# 4) Índices Urbanísticos (render)
# =============================
def _card(title: str, value: Any, suffix: str = "") -> None:
    if value is None or value == "":
        st.metric(title, "—")
    else:
        st.metric(title, f"{value}{suffix}")

render_indices_section(
    calc=st.session_state.calc,
    pick_func=pick_rule,
    card_func=_card,
)


# =============================
# 5) Análise Urbanística
# =============================
render_analise_section(
    st.session_state.calc,
    lot_area=lot_area,
    built_ground=built_ground,
    permeable_area=permeable_area,
    pick_func=pick_value,   # pega campos dentro da rule
)


# =============================
# 6) Relatório Urbanístico
# =============================
render_relatorio_section(st.session_state.calc)
