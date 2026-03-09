import os
import json
import pathlib
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st

# =============================
# Debug markers (garante que o deploy está lendo o app.py correto)
# =============================
st.write("APP VERSION MARKER: 2026-03-09-CREDITS-PANEL-V1")
st.write("CWD:", os.getcwd())
st.write("FILES in data/:", [p.name for p in pathlib.Path("data").glob("*")])

# =============================
# Config
# =============================
st.set_page_config(layout="wide", page_title="Viabilidade")

DATA_DIR = Path("data")
ZONE_FILE = DATA_DIR / "zoneamento_light.json"

# =============================
# Imports do projeto (robustos)
# =============================
try:
    from core.zones_map import load_zones
except Exception:
    from core.zones_mapa import load_zones  # type: ignore

try:
    from core.streets import load_streets  # noqa
except Exception:
    load_streets = None  # type: ignore

try:
    from core.supabase_rules import fetch_rule, pick_rule  # type: ignore
except Exception:
    from core.supabase_rule import fetch_rule, pick_rule  # type: ignore

from ui.mapa import render_mapa_section
from ui.lote import render_lote_section
from ui.localizacao import render_localizacao_section
from ui.indices import render_indices_section
from ui.analise import render_analise_section
from ui.relatorio import render_relatorio_section
from core.auth import handle_oauth_callback
from ui.auth_panel import render_google_login_top
from ui.credits_panel import render_credits_panel


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


# =============================
# Pequena função de card (evita dependência externa)
# =============================
def _card(title: str, value: Any, suffix: str = "") -> None:
    v = "—" if value is None or value == "" else f"{value}{suffix}"
    st.markdown(
        f"""
        <div style="padding:12px;border:1px solid #e7e7e7;border-radius:12px;margin-bottom:10px;">
            <div style="font-size:12px;opacity:.75">{title}</div>
            <div style="font-size:20px;font-weight:700">{v}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================
# Estado inicial
# =============================
if "selected_lat" not in st.session_state:
    st.session_state.selected_lat = None
if "selected_lon" not in st.session_state:
    st.session_state.selected_lon = None
if "calc" not in st.session_state or not isinstance(st.session_state.calc, dict):
    st.session_state.calc = {}
st.session_state.calc.setdefault("use_type_code", "RES_UNI")

# Auth callback precisa rodar cedo, antes de renderizar a UI principal
handle_oauth_callback()

# =============================
# Carregar bases
# =============================
zones_gj = _zones_geojson()
zones_prepared = _zones_prepared()

# =============================
# UI topo
# =============================
st.title("Viabilidade")
render_google_login_top()
render_credits_panel(_card)
st.divider()


# =============================
# 1) Mapa (seleciona lat/lon e define raio)
# =============================
radius_m = render_mapa_section(zones_gj)

# Botão (mantém o fluxo)
calcular = st.button("🔎 Calcular viabilidade", key="btn_calc")

# =============================
# 2) Dados do lote (RETORNA 3 valores SEM erro)
# =============================
lot_area, built_ground, permeable_area = render_lote_section()

st.session_state.calc["lot_area_m2"] = float(lot_area)
st.session_state.calc["lot_front_m"] = float(st.session_state.get("lot_front_m") or 0.0)
st.session_state.calc["lot_depth_m"] = float(st.session_state.get("lot_depth_m") or 0.0)
st.session_state.calc["lot_is_corner"] = bool(st.session_state.get("lot_is_corner", False))

# =============================
# 3) Localização (zona + via)
# =============================
_ = render_localizacao_section(calcular, zones_prepared, radius_m)

# =============================
# Garantir que a REGRA vem do Supabase assim que tiver zona
# =============================
calc = st.session_state.calc
if calcular and calc.get("zone") and not calc.get("rule") and not calc.get("err"):
    try:
        rule = fetch_rule(calc["zone"], calc.get("use_type_code") or "RES_UNI")
        if rule:
            calc["rule"] = rule
        else:
            calc["err"] = f"Nenhuma regra no Supabase para zona={calc['zone']} e uso={calc.get('use_type_code')}"
    except Exception as e:
        calc["err"] = f"Erro ao consultar Supabase: {e}"

# =============================
# 4) Índices Urbanísticos (Supabase)
# =============================
render_indices_section(calc=calc, card_func=_card, pick_func=pick_rule, get_rule_func=fetch_rule)

# =============================
# 5) Análise Urbanística
# =============================
render_analise_section(
    calc,
    lot_area=lot_area,
    built_ground=built_ground,
    permeable_area=permeable_area,
    pick_func=pick_rule,
)

# =============================
# 6) Relatório Urbanístico
# =============================
render_relatorio_section(calc)
