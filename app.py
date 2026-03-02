from __future__ import annotations

import uuid
import json
from pathlib import Path
from typing import Any, Optional, Dict

import streamlit as st
import folium
from streamlit_folium import st_folium

# FIX: módulo correto é zones_map.py (não zones_mapa.py)
from core.zones_map import load_zones, zone_from_latlon  # type: ignore
from core.streets import find_street
from core.zone_rules_repository import get_zone_rule

from ui.mapa import render_mapa_section
from ui.lote import render_lote_section
from ui.localizacao import render_localizacao_section
from ui.indices import render_indices_section
from ui.analise import render_analise_section
from ui.relatorio import render_relatorio_section

APP_TITLE = "Viabilidade"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ZONE_FILE = DATA_DIR / "zoneamento_light.json"


@st.cache_resource(show_spinner=False)
def _zones():
    with ZONE_FILE.open("r", encoding="utf-8") as f:
        gj = json.load(f)
    return {"prepared": load_zones(ZONE_FILE), "geojson": gj}


def _as_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        return float(x)
    except Exception:
        return None


def _pick(rule: Dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in rule and rule.get(k) is not None:
            return rule.get(k)
    return None


def _fmt(v: Any, suffix: str = "") -> str:
    if v is None or v == "":
        return "—"
    if isinstance(v, (int, float)):
        if isinstance(v, float) and abs(v - round(v)) < 1e-9:
            v = int(round(v))
        return f"{v}{suffix}"
    return f"{v}{suffix}"


def _card(title: str, value: Any, suffix: str = ""):
    st.markdown(
        f"""
        <div style="
            border:1px solid rgba(0,0,0,.08);
            border-radius:14px;
            padding:14px 14px 10px 14px;
            background:#fff;
            height:86px;
        ">
          <div style="font-size:12px; opacity:.7; margin-bottom:6px;">{title}</div>
          <div style="font-size:22px; font-weight:700;">{_fmt(value, suffix)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _ensure_state():
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    if "last_click" not in st.session_state:
        st.session_state.last_click = None

    if "click_hash" not in st.session_state:
        st.session_state.click_hash = None

    if "calc" not in st.session_state:
        st.session_state.calc = {
            "lat": None,
            "lon": None,
            "zone": None,
            "street_info": None,
            "rule": None,
            "use_type_code": "RES_UNI",
            "radius_m": 100,
            "ok": False,
            "err": None,
        }


st.set_page_config(layout="wide", page_title=APP_TITLE)
st.title(APP_TITLE)

_ensure_state()
zones = _zones()
zones_gj = zones["geojson"]

# 1) Mapa
radius_m = render_mapa_section(zones_gj)

st.divider()

# 2) Lote
lot_area, testada, profundidade, built_ground = render_lote_section()

st.divider()

# 3) Localização (zona + via)
render_localizacao_section(
    calcular=None,  # o botão fica no mapa, se seu módulo usa outro fluxo ajuste aqui
    zones_prepared=zones["prepared"],
    radius_m=int(radius_m),
)

st.divider()

# 4) Índices (Supabase)
render_indices_section(
    calc=st.session_state.calc,
    pick_func=_pick,
    card_func=_card,
)

st.divider()

# 5) Análise (cálculos simples)
render_analise_section(
    lot_area=lot_area,
    built_ground=built_ground,
    testada=testada,
    profundidade=profundidade,
    pick_func=_pick,
    as_float_func=_as_float,
)

st.divider()

# 6) Relatório (perguntas e respostas)
render_relatorio_section(
    lot_area=lot_area,
    testada=testada,
    profundidade=profundidade,
    built_ground=built_ground,
    pick_func=_pick,
    as_float_func=_as_float,
)
