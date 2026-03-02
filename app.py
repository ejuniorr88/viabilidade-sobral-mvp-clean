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
from core.ui_localizacao import render_localizacao_section
from core.ui_indices import render_indices_section

APP_TITLE = "Viabilidade"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ZONE_FILE = DATA_DIR / "zoneamento_light.json"


# =============================
# Helpers
# =============================

@st.cache_resource(show_spinner=False)
def _zones():
    with ZONE_FILE.open("r", encoding="utf-8") as f:
        gj = json.load(f)
    return {"prepared": load_zones(ZONE_FILE), "geojson": gj}


def _render_map(zones_gj, lat0=-3.689, lon0=-40.349, click_lat=None, click_lon=None):
    m = folium.Map(
        location=[lat0, lon0],
        zoom_start=12,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    folium.GeoJson(
        zones_gj,
        name="Zonas",
        style_function=lambda _: {"fillOpacity": 0.08, "weight": 1},
        tooltip=folium.GeoJsonTooltip(fields=["sigla"], aliases=["Zona"]),
    ).add_to(m)

    if click_lat is not None and click_lon is not None:
        folium.Marker(
            location=[click_lat, click_lon],
            tooltip="Ponto selecionado",
        ).add_to(m)

    folium.LayerControl(collapsed=True).add_to(m)
    return m


def _as_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        return float(x)
    except Exception:
        return None


def _pick(rule: Dict[str, Any], *keys: str) -> Any:
    """Return first non-None value for given keys."""
    for k in keys:
        if k in rule and rule.get(k) is not None:
            return rule.get(k)
    return None


def _fmt(v: Any, suffix: str = "") -> str:
    if v is None or v == "":
        return "—"
    if isinstance(v, (int, float)):
        # avoid 1.0 showing as 1.0 when it's integer-like
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

    # computed results (only after clicking "Calcular viabilidade")
    if "calc" not in st.session_state:
        st.session_state.calc = {
            "lat": None,
            "lon": None,
            "zone": None,
            "street_info": None,
            "rule": None,
            "use_type_code": "RES_UNI",
	            # manter como int para compatibilidade com st.number_input
	            "radius_m": 100,
            "ok": False,
            "err": None,
        }


# =============================
# App
# =============================

st.set_page_config(layout="wide", page_title=APP_TITLE)
st.title(APP_TITLE)

_ensure_state()
zones = _zones()
zones_gj = zones["geojson"]

# =============================
# 1) Selecione o ponto no mapa
# =============================

st.subheader("1) Selecione o ponto no mapa")

radius_m = st.number_input(
    "Raio para encontrar via (m)",
    min_value=10,
    max_value=100000,
    # IMPORTANT: Streamlit não aceita misturar tipos numéricos (int vs float)
    # no number_input. Mantemos tudo como int aqui.
    value=int(st.session_state.calc.get("radius_m") or 100),
    step=10,
)

# Render map with last click marker
last_click = st.session_state.last_click
m = _render_map(
    zones_gj,
    click_lat=last_click["lat"] if last_click else None,
    click_lon=last_click["lon"] if last_click else None,
)
out = st_folium(m, width=None, height=420)

# Single-click update (forces rerun so marker appears immediately)
if out and out.get("last_clicked"):
    new_lat = float(out["last_clicked"]["lat"])
    new_lon = float(out["last_clicked"]["lng"])
    new_hash = f"{new_lat:.8f}_{new_lon:.8f}"

    if new_hash != st.session_state.click_hash:
        st.session_state.last_click = {"lat": new_lat, "lon": new_lon}
        st.session_state.click_hash = new_hash

        # when click changes, mark results as not calculated yet
        st.session_state.calc["ok"] = False
        st.session_state.calc["err"] = None
        st.rerun()

# show coordinates caption
if st.session_state.last_click:
    st.caption(
        f"📍 Coordenadas selecionadas: "
        f"lat {st.session_state.last_click['lat']:.6f} | "
        f"lon {st.session_state.last_click['lon']:.6f}"
    )

calcular = st.button(
    "🔎 Calcular viabilidade",
    type="primary",
    disabled=not st.session_state.last_click,
)

st.divider()

# =============================
# 2) Dados do lote
# =============================

st.subheader("2) Dados do lote")

col1, col2, col3 = st.columns(3)
with col1:
    lot_area = st.number_input("Área do lote (m²)", min_value=1.0, value=300.0, step=10.0)
with col2:
    testada = st.number_input("Largura (testada) (m)", min_value=1.0, value=10.0, step=0.5)
with col3:
    profundidade = st.number_input("Profundidade (m)", min_value=1.0, value=30.0, step=0.5)

built_ground = st.number_input("Área pretendida no térreo (m²)", min_value=0.0, value=0.0, step=5.0)

st.divider()

# =============================
# 3) Localização (zona + via) (MODULARIZADO)
# =============================

render_localizacao_section(
    calcular=calcular,
    zones_prepared=zones["prepared"],
    radius_m=int(radius_m),
)

# read computed results (mantido para os blocos seguintes)
calc = st.session_state.calc
zone = calc.get("zone")
street_info = calc.get("street_info")

st.divider()

# =============================
# 4) Índices Urbanísticos (Supabase)
# =============================

# =============================
# 4) Índices Urbanísticos (Supabase) (MODULARIZADO)
# =============================

render_indices_section(
    calc=st.session_state.calc,
    pick_func=_pick,
    card_func=_card,
)

st.divider()

# =============================
# 5) Análise Urbanística
# =============================

st.subheader("5) Análise Urbanística")

if not calc.get("ok"):
    st.info("Clique em **Calcular viabilidade** para gerar a análise.")
elif not rule:
    st.info("Sem regra do Supabase — não é possível validar índices.")
else:
    # Pull values safely
    to_max_f = _as_float(_pick(rule, "to_max_pct", "to_max"))
    ia_max_f = _as_float(_pick(rule, "ia_max", "ia_maximo"))
    tp_min_f = _as_float(_pick(rule, "tp_min_pct", "tp_min"))

    # Compute used metrics
    ia_utilizado = (built_ground / lot_area) if lot_area else 0.0
    to_utilizada = ((built_ground / lot_area) * 100) if lot_area else 0.0

    # TP prevista: não temos área permeável informada aqui; manter como 0 (ou pedir input depois)
    tp_prevista = 0.0

    st.write(f"IA utilizado: **{ia_utilizado:.2f}**")
    st.write(f"TO utilizada: **{to_utilizada:.1f}%**")
    st.write(f"TP prevista: **{tp_prevista:.1f}%**")

    # Validations (only if rule has values)
    if to_max_f is not None:
        if to_utilizada <= to_max_f:
            st.success("✅ Taxa de Ocupação dentro do permitido")
        else:
            st.error("❌ Taxa de Ocupação EXCEDE o permitido")

    if ia_max_f is not None:
        if ia_utilizado <= ia_max_f:
            st.success("✅ Índice de Aproveitamento dentro do permitido")
        else:
            st.error("❌ Índice de Aproveitamento EXCEDE o permitido")

    if tp_min_f is not None:
        if tp_prevista >= tp_min_f:
            st.success("✅ Taxa de Permeabilidade atende o mínimo")
        else:
            st.warning("⚠️ Taxa de Permeabilidade ainda não foi informada / está abaixo do mínimo (precisamos do input de área permeável).")
