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
# 3) Localização (zona + via)
# =============================

st.subheader("3) Localização (zona + via)")

# use_type_code placed here because it affects Supabase rule (keeps flow clear)
use_type_code = st.text_input("use_type_code", value=st.session_state.calc.get("use_type_code") or "RES_UNI")

# run calculations ONLY when button pressed
if calcular and st.session_state.last_click:
    lat = st.session_state.last_click["lat"]
    lon = st.session_state.last_click["lon"]

    st.session_state.calc["lat"] = lat
    st.session_state.calc["lon"] = lon
    st.session_state.calc["use_type_code"] = use_type_code
    st.session_state.calc["radius_m"] = int(radius_m)

    # zone + street
    zone = zone_from_latlon(zones["prepared"], lat, lon)
    street_info = find_street(lat=lat, lon=lon, radius_m=float(radius_m))

    st.session_state.calc["zone"] = zone
    st.session_state.calc["street_info"] = street_info

    # supabase rule
    rule = None
    err = None
    try:
        if zone:
            rule = get_zone_rule(zone, use_type_code)
        else:
            err = "Clique fora das zonas."
    except Exception as e:
        err = f"Erro ao consultar Supabase: {e}"

    st.session_state.calc["rule"] = rule
    st.session_state.calc["err"] = err
    st.session_state.calc["ok"] = True

# read computed results
calc = st.session_state.calc
zone = calc.get("zone")
street_info = calc.get("street_info")

# show location cards
colA, colB, colC = st.columns(3)
with colA:
    st.write("Zona")
    st.write(zone or "—")
with colB:
    st.write("Rua / Logradouro")
    st.write(street_info["name"] if street_info else "—")
with colC:
    st.write("Tipo de via")
    st.write(street_info["type"] if street_info else "—")

if street_info and "distance_m" in street_info:
    st.caption(
        f"Distância até o eixo da via: {float(street_info['distance_m']):.1f} m "
        f"(raio {float(calc.get('radius_m') or radius_m):.0f} m)."
    )

if calc.get("err"):
    st.warning(str(calc["err"]))

st.divider()

# =============================
# 4) Índices Urbanísticos (Supabase)
# =============================

st.subheader("4) Índices Urbanísticos (Supabase)")

rule = calc.get("rule") if calc.get("ok") else None

if not calc.get("ok"):
    st.info("Clique em **Calcular viabilidade** para carregar zona, via e regras do Supabase.")
elif zone and not rule and not calc.get("err"):
    st.warning("Nenhuma regra encontrada para (zona + uso) no Supabase.")
elif rule:
    # Map fields (support multiple key names)
    to_max = _pick(rule, "to_max_pct", "to_max", "taxa_ocupacao_max_pct", "to")
    tp_min = _pick(rule, "tp_min_pct", "tp_min", "taxa_permeabilidade_min_pct", "tp")
    # TO do subsolo aparece com nomes diferentes em versões do dump.
    to_subsolo = _pick(
        rule,
        "to_subsolo_max_pct",
        "to_subsolo_pct",
        "to_subsolo",
        "to_subsolo_max",
        "to_subsolo_maximo_pct",
        "to_subsolo_maximo",
        "to_subsolo_max_percent",
        "to_subsolo_maxima_pct",
        "tos_max_pct",
    )
    ia_max = _pick(rule, "ia_max", "ia_maximo", "indice_aproveitamento_max")
    ia_min = _pick(rule, "ia_min", "ia_minimo", "indice_aproveitamento_min")
    rec_frente = _pick(rule, "recuo_frontal_m", "recuo_frente_m", "recuo_frente")
    rec_fundo = _pick(rule, "recuo_fundo_m", "recuo_fundos_m", "recuo_fundo")
    rec_lateral = _pick(rule, "recuo_lateral_m", "recuo_lateral")
    area_min = _pick(rule, "area_min_lote_m2", "area_min_lote", "lote_area_min_m2")
    area_max = _pick(rule, "area_max_lote_m2", "area_max_lote", "lote_area_max_m2")
    test_min = _pick(
        rule,
        "testada_min_m",
        "testada_min",
        "lote_testada_min_m",
        "testada_minima_m",
        "testada_minima",
        "testada_minima_lote_m",
        "testada_minima_lote",
        "frontage_min_m",
    )
    test_max = _pick(
        rule,
        "testada_max_m",
        "testada_max",
        "lote_testada_max_m",
        "testada_maxima_m",
        "testada_maxima",
        "testada_maxima_lote_m",
        "testada_maxima_lote",
        "frontage_max_m",
    )
    # gabarito/altura
    altura_max = _pick(rule, "altura_max_m", "gabarito_m", "altura_maxima_m", "altura_max")

    # Layout cards
    c1, c2, c3 = st.columns(3)
    with c1:
        _card("Zona", zone)
    with c2:
        _card("Taxa de Permeabilidade (TP) mínima", tp_min, "%")
    with c3:
        _card("Taxa de Ocupação (TO) máxima", to_max, "%")

    c4, c5, c6 = st.columns(3)
    with c4:
        _card("TO do Subsolo máxima", to_subsolo, "%")
    with c5:
        _card("Índice de Aproveitamento (IA) máximo", ia_max)
    with c6:
        _card("Índice de Aproveitamento (IA) mínimo", ia_min)

    c7, c8, c9 = st.columns(3)
    with c7:
        _card("Recuo de Frente", rec_frente, " m")
    with c8:
        _card("Recuo de Fundo", rec_fundo, " m")
    with c9:
        _card("Recuo Lateral", rec_lateral, " m")

    c10, c11, c12 = st.columns(3)
    with c10:
        _card("Área mínima do lote", area_min, " m²")
    with c11:
        _card("Testada mínima", test_min, " m")
    with c12:
        _card("Altura máxima (gabarito)", altura_max, " m")

    c13, c14, _ = st.columns(3)
    with c13:
        _card("Área máxima do lote", area_max, " m²")
    with c14:
        _card("Testada máxima", test_max, " m")

    with st.expander("Ver regra bruta (JSON do Supabase)", expanded=False):
        st.json(rule)

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
