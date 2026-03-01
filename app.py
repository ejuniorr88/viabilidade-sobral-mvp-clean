from __future__ import annotations

import uuid
from pathlib import Path
import json
from typing import Any, Optional, Dict, Iterable

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
    return {
        "prepared": load_zones(ZONE_FILE),
        "geojson": gj,
    }


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


def _first_value(rule: Optional[Dict[str, Any]], keys: Iterable[str]) -> Any:
    """Return the first non-None value found among keys in a dict-like rule."""
    if not rule:
        return None
    for k in keys:
        if k in rule and rule.get(k) is not None:
            return rule.get(k)
    return None


def _to_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except Exception:
        return None


def _fmt(v: Any, suffix: str = "") -> str:
    if v is None:
        return "—"
    try:
        if isinstance(v, bool):
            return "Sim" if v else "Não"
        if isinstance(v, (int, float)):
            # keep 2 decimals for floats, 0 for ints
            if float(v).is_integer():
                return f"{int(v)}{suffix}"
            return f"{float(v):.2f}{suffix}"
        return f"{v}{suffix}"
    except Exception:
        return f"{v}{suffix}"


# =============================
# App
# =============================

st.set_page_config(layout="wide", page_title=APP_TITLE)
st.title(APP_TITLE)

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

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
    value=100,
    step=10,
)

# Controle seguro de clique (clique único real)
if "last_click" not in st.session_state:
    st.session_state.last_click = None
if "click_hash" not in st.session_state:
    st.session_state.click_hash = None

last_click = st.session_state.last_click

m = _render_map(
    zones_gj,
    click_lat=last_click["lat"] if last_click else None,
    click_lon=last_click["lon"] if last_click else None,
)
out = st_folium(m, width=None, height=420)

# Atualiza ponto e força rerun exatamente uma vez
if out and out.get("last_clicked"):
    new_lat = float(out["last_clicked"]["lat"])
    new_lon = float(out["last_clicked"]["lng"])
    new_hash = f"{new_lat:.8f}_{new_lon:.8f}"

    if new_hash != st.session_state.click_hash:
        st.session_state.last_click = {"lat": new_lat, "lon": new_lon}
        st.session_state.click_hash = new_hash

        # invalida cálculo anterior (se existir)
        st.session_state.calc_ready = False
        st.session_state.calc_hash = None
        st.rerun()

# Mostrar coordenadas
if st.session_state.last_click:
    st.caption(
        f"📍 Coordenadas selecionadas: "
        f"lat {st.session_state.last_click['lat']:.6f} | "
        f"lon {st.session_state.last_click['lon']:.6f}"
    )

# Botão de cálculo: grava estado e mantém resultados até novo clique
if "calc_ready" not in st.session_state:
    st.session_state.calc_ready = False
if "calc_hash" not in st.session_state:
    st.session_state.calc_hash = None

calcular = st.button(
    "🔎 Calcular viabilidade",
    type="primary",
    disabled=not st.session_state.last_click,
)

if calcular and st.session_state.last_click:
    st.session_state.calc_ready = True
    st.session_state.calc_hash = st.session_state.click_hash

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

col4, col5, col6 = st.columns(3)
with col4:
    built_ground = st.number_input("Área pretendida no térreo (m²)", min_value=0.0, value=0.0, step=5.0)
with col5:
    built_total = st.number_input("Área total construída pretendida (m²)", min_value=0.0, value=0.0, step=10.0)
with col6:
    permeable_area = st.number_input("Área permeável prevista (m²)", min_value=0.0, value=0.0, step=5.0)

st.divider()


# =============================
# Pré-cálculo (zona + via + regra) só quando calc_ready
# =============================

lat = lon = None
zone = None
street_info = None
rule = None

if st.session_state.calc_ready and st.session_state.last_click and st.session_state.calc_hash == st.session_state.click_hash:
    lat = st.session_state.last_click["lat"]
    lon = st.session_state.last_click["lon"]
    zone = zone_from_latlon(zones["prepared"], lat, lon)
    street_info = find_street(lat=lat, lon=lon, radius_m=float(radius_m))
else:
    st.info("Clique no mapa e depois em **Calcular viabilidade** para ver os resultados.")

# =============================
# 3) Localização (zona + via)
# =============================

st.subheader("3) Localização (zona + via)")

if st.session_state.calc_ready and st.session_state.last_click and st.session_state.calc_hash == st.session_state.click_hash:
    if zone:
        st.success(f"Zona detectada: {zone}")
    else:
        st.warning("Clique fora das zonas.")

    colA, colB, colC = st.columns(3)
    with colA:
        st.write("**Zona**")
        st.write(zone or "—")
    with colB:
        st.write("**Rua / Logradouro**")
        st.write(street_info["name"] if street_info else "Via não encontrada")
    with colC:
        st.write("**Tipo de via**")
        st.write(street_info["type"] if street_info else "—")

    if street_info:
        st.caption(
            f"Distância até o eixo da via: {street_info['distance_m']:.1f} m "
            f"(raio {radius_m:.0f} m)."
        )
    else:
        st.warning(f"Via não encontrada dentro de {radius_m:.0f} m.")

st.divider()


# =============================
# 4) Índices Urbanísticos (Supabase)
# =============================

st.subheader("4) Índices Urbanísticos")

use_type_code = st.text_input("use_type_code", value="RES_UNI")

if st.session_state.calc_ready and zone:
    try:
        rule = get_zone_rule(zone, use_type_code)
    except Exception as e:
        rule = None
        st.error(f"Erro ao consultar Supabase: {e}")

    if not rule:
        st.warning("Nenhuma regra encontrada para (zona + uso).")

# Normaliza chaves (porque o schema pode variar)
to_max_pct = _to_float(_first_value(rule, ["to_max_pct", "to_max", "taxa_ocupacao_max", "taxa_ocupacao_max_pct"]))
to_subsoil_max_pct = _to_float(_first_value(rule, [
    "to_subsoil_max_pct",
    "to_subsolo_max_pct",
    "to_subsolo_pct",
    "taxa_ocupacao_subsolo_max",
    "taxa_ocupacao_subsolo_max_pct",
]))
ia_max = _to_float(_first_value(rule, ["ia_max", "ia_maximo", "ia_max_ratio", "ia_maximum"]))
ia_min = _to_float(_first_value(rule, ["ia_min", "ia_minimo", "ia_min_ratio", "ia_minimum"]))
tp_min_pct = _to_float(_first_value(rule, ["tp_min_pct", "tp_min", "permeabilidade_min", "permeabilidade_min_pct"]))
height_max_m = _to_float(_first_value(rule, ["height_max_m", "altura_max_m", "height_max", "altura_max"]))
front_setback_m = _to_float(_first_value(rule, ["setback_front_m", "recuo_frontal_m", "setback_front", "recuo_frontal"]))
side_setback_m = _to_float(_first_value(rule, ["setback_side_m", "recuo_lateral_m", "setback_side", "recuo_lateral"]))
back_setback_m = _to_float(_first_value(rule, ["setback_back_m", "recuo_fundos_m", "setback_back", "recuo_fundos"]))

lot_area_min_m2 = _to_float(_first_value(rule, [
    "lot_area_min_m2",
    "area_min_lote_m2",
    "area_min_lote",
    "area_lote_min",
]))
lot_area_max_m2 = _to_float(_first_value(rule, [
    "lot_area_max_m2",
    "area_max_lote_m2",
    "area_max_lote",
    "area_lote_max",
]))

frontage_min_m = _to_float(_first_value(rule, [
    "frontage_min_m",
    "testada_min_m",
    "testada_min",
]))
frontage_max_m = _to_float(_first_value(rule, [
    "frontage_max_m",
    "testada_max_m",
    "testada_max",
    "testada_maxima",
]))
allow_attach_one_side = _first_value(rule, ["allow_attach_one_side"])
notes = _first_value(rule, ["notes", "observacoes", "obs"])

if st.session_state.calc_ready and zone:
    # Quadro “bacana” com TODOS os parâmetros solicitados
    def _val(v: Any, suffix: str = "") -> str:
        return _fmt(v, suffix) if v is not None else "—"

    c1, c2, c3 = st.columns(3)
    c1.metric("Zona", zone)
    c2.metric("Taxa de permeabilidade (TP mínima)", _val(tp_min_pct, "%"))
    c3.metric("Taxa de ocupação (TO máxima)", _val(to_max_pct, "%"))

    c4, c5, c6 = st.columns(3)
    c4.metric("TO do subsolo (máx.)", _val(to_subsoil_max_pct, "%"))
    c5.metric("Índice de aproveitamento (IA máximo)", _val(ia_max))
    c6.metric("Índice de aproveitamento (IA mínimo)", _val(ia_min))

    c7, c8, c9 = st.columns(3)
    c7.metric("Recuo de frente", _val(front_setback_m, " m"))
    c8.metric("Recuo de fundo", _val(back_setback_m, " m"))
    c9.metric("Recuo de lateral", _val(side_setback_m, " m"))

    c10, c11, c12 = st.columns(3)
    c10.metric("Área mínima do lote", _val(lot_area_min_m2, " m²"))
    c11.metric("Testada mínima", _val(frontage_min_m, " m"))
    c12.metric("Altura máxima permitida", _val(height_max_m, " m"))

    c13, c14, c15 = st.columns(3)
    c13.metric("Área máxima do lote", _val(lot_area_max_m2, " m²"))
    c14.metric("Testada máxima", _val(frontage_max_m, " m"))
    c15.metric("Pode encostar em 1 lado", _val(allow_attach_one_side))

    if notes:
        st.info(f"**Observações:** {notes}")

    with st.expander("Debug (regra completa)", expanded=False):
        st.json(rule, expanded=True)

st.divider()


# =============================
# 5) Análise Urbanística
# =============================

st.subheader("5) Análise Urbanística")

if st.session_state.calc_ready and zone:
    # Cálculos do lote
    ia_used = (built_total / lot_area) if lot_area > 0 else 0.0
    to_used_pct = (built_ground / lot_area * 100.0) if lot_area > 0 else 0.0
    tp_used_pct = (permeable_area / lot_area * 100.0) if lot_area > 0 else 0.0

    st.write(f"IA utilizado: **{ia_used:.2f}**")
    st.write(f"TO utilizada: **{to_used_pct:.1f}%**")
    st.write(f"TP prevista: **{tp_used_pct:.1f}%**")

    # IA
    if ia_max is not None:
        if ia_used <= ia_max + 1e-9:
            st.success("✓ Índice de Aproveitamento dentro do permitido")
        else:
            st.error("✗ Índice de Aproveitamento acima do permitido")
    else:
        st.warning("IA máximo não informado na regra (Supabase).")

    # TO
    if to_max_pct is not None:
        if to_used_pct <= to_max_pct + 1e-9:
            st.success("✓ Taxa de Ocupação dentro do permitido")
        else:
            st.error("✗ Taxa de Ocupação acima do permitido")
    else:
        st.warning("TO máxima não informada na regra (Supabase).")

    # TP
    if tp_min_pct is not None:
        if tp_used_pct + 1e-9 >= tp_min_pct:
            st.success("✓ Taxa de Permeabilidade atende ao mínimo")
        else:
            st.error("✗ Taxa de Permeabilidade abaixo do mínimo")
    else:
        st.warning("TP mínima não informada na regra (Supabase).")

    # Observação: altura / recuos não dá pra checar sem inputs do projeto
    st.caption("Recuos e altura máxima são exibidos no quadro acima; checagens dependem do projeto arquitetônico (implantação/cortes).")

