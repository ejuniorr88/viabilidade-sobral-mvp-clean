from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st

from core.calculations import calculate_basic_indices
from core.streets import find_street
from core.zone_rules_repository import get_zone_rule
from core.zones_map import load_geojson, load_zones, find_zone

from ui.lote import render_lote_section
from ui.mapa import render_mapa_section
from ui.localizacao import render_localizacao_section
from ui.indices import render_indices_section
from ui.analise import render_analise_section
from ui.relatorio import render_relatorio_section


# =============================
# Config
# =============================
st.set_page_config(layout="wide", page_title="Viabilidade")
st.title("Viabilidade")

DATA_DIR = Path("data")
ZONE_FILE = DATA_DIR / "zoneamento_light.json"  # existe no repo
RUAS_FILE = DATA_DIR / "ruas.json"              # existe no repo


@st.cache_data(show_spinner=False)
def _zones_geojson() -> Dict[str, Any]:
    return load_geojson(ZONE_FILE)


@st.cache_data(show_spinner=False)
def _zones_prepared() -> Any:
    # lista de dicts com geometry preparada
    return load_zones(ZONE_FILE)


@st.cache_data(show_spinner=False)
def _streets_geojson() -> Dict[str, Any]:
    # ui/localizacao usa find_street() que carrega internamente, mas aqui mantemos o arquivo validado
    with open(RUAS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_lote_defaults() -> Dict[str, float]:
    return {
        "area": 300.0,
        "testada": 10.0,
        "profundidade": 30.0,
    }


# =============================
# Estado
# =============================
if "lote" not in st.session_state:
    st.session_state.lote = _get_lote_defaults()

if "use_type_code" not in st.session_state:
    st.session_state.use_type_code = "RES_UNI"


# =============================
# 1) Dados do lote
# =============================
st.session_state.lote = render_lote_section(st.session_state.lote)


# =============================
# 2) Mapa
# =============================
zones_gj = _zones_geojson()
_ = _streets_geojson()  # só valida arquivo e evita FileNotFound silencioso

latlon = render_mapa_section(zones_gj)


# =============================
# 3) Localização
# =============================
street_info = render_localizacao_section(latlon)

# Determinar zona pelo ponto (se houver)
zone_sigla: Optional[str] = None
via_tipo: str = "-"

if latlon and latlon.get("lat") is not None and latlon.get("lon") is not None:
    prepared = _zones_prepared()
    zone_sigla = find_zone(prepared, latlon["lat"], latlon["lon"])

if street_info and isinstance(street_info, dict):
    # tenta achar um campo de tipo de via
    via_tipo = (
        street_info.get("tipo")
        or street_info.get("type")
        or street_info.get("via_tipo")
        or "via local"
    )


# =============================
# 4) Índices Urbanísticos (Supabase)
# =============================
st.subheader("4) Índices Urbanísticos (Supabase)")

use_type_code = st.selectbox(
    "Uso principal",
    options=["RES_UNI", "RES_MULTI", "COM_SERV"],
    index=["RES_UNI", "RES_MULTI", "COM_SERV"].index(st.session_state.use_type_code)
    if st.session_state.use_type_code in ["RES_UNI", "RES_MULTI", "COM_SERV"]
    else 0,
)

st.session_state.use_type_code = use_type_code

if not zone_sigla:
    st.info("Selecione um ponto no mapa para identificar a zona.")

calc: Dict[str, Any] = {}
rule: Dict[str, Any] = {}

btn = st.button("Calcular viabilidade")

if btn:
    if not zone_sigla:
        st.error("Não foi possível identificar a zona. Selecione um ponto dentro do perímetro do zoneamento.")
    else:
        # 1) regra do supabase
        rule = get_zone_rule(zone_sigla, use_type_code, subzone_code="")

        # 2) cálculos básicos
        lote = st.session_state.lote
        calc = calculate_basic_indices(lote_area=float(lote.get("area", 0.0)), rule=rule)

        # 3) “coloca” recuos no calc para o relatório/analise (compat)
        calc["front_setback_m"] = rule.get("front_setback_m")
        calc["side_setback_m"] = rule.get("side_setback_m")
        calc["rear_setback_m"] = rule.get("rear_setback_m")

        # 4) exibe
        render_indices_section(rule=rule, calc=calc)
        render_analise_section(calc=calc, zone_sigla=zone_sigla, via_tipo=via_tipo)
        render_relatorio_section(
            zone_sigla=zone_sigla,
            via_tipo=via_tipo,
            lote=lote,
            calc=calc,
            rule=rule,
            street_info=street_info,
            zoning_info={"zone_sigla": zone_sigla},
        )
