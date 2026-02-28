from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import folium
import streamlit as st
from streamlit_folium import st_folium

from shapely.geometry import Point, shape
from shapely.ops import transform as shp_transform
from shapely.strtree import STRtree
from pyproj import Transformer

from core.zone_rules_repository import get_zone_rule
from core.zones_map import load_zones, zone_from_latlon
from core.calculations import compute
from core.supabase_client import get_supabase


APP_VERSION = "v1.1-streets"
APP_TITLE = "Viabilidade (v1.1)"
DATA_DIR = Path(__file__).parent / "data"
ZONE_FILE = DATA_DIR / "zoneamento_light.json"
RUAS_FILE = DATA_DIR / "ruas.json"


@st.cache_resource(show_spinner=False)
def _zones():
    # load_zones -> lista preparada (shapely) para lookup
    # Para desenhar no mapa, também precisamos do GeoJSON bruto.
    with ZONE_FILE.open("r", encoding="utf-8") as f:
        gj = json.load(f)
    return {"prepared": load_zones(ZONE_FILE), "geojson": gj}


@st.cache_resource(show_spinner=False)
def _streets_index() -> dict[str, Any]:
    """Carrega ruas e cria índice espacial em UTM (m).

    Espera GeoJSON FeatureCollection em RUAS_FILE.
    Usa EPSG:31984 (SIRGAS 2000 / UTM 24S) para medir distância em metros.
    """
    if not RUAS_FILE.exists():
        return {"ok": False, "reason": f"Arquivo não encontrado: {RUAS_FILE}"}

    import json

    with open(RUAS_FILE, "r", encoding="utf-8") as f:
        gj = json.load(f)

    feats = gj.get("features", [])

    # Transformador para medir em metros (UTM 24S SIRGAS 2000)
    ll_to_utm = Transformer.from_crs("EPSG:4326", "EPSG:31984", always_xy=True).transform

    geoms_utm = []
    props_list = []
    for feat in feats:
        geom = feat.get("geometry")
        if not geom:
            continue
        try:
            g_ll = shape(geom)
            g_utm = shp_transform(ll_to_utm, g_ll)
            geoms_utm.append(g_utm)
            props_list.append(feat.get("properties", {}) or {})
        except Exception:
            continue

    if not geoms_utm:
        return {"ok": False, "reason": "Nenhuma geometria de rua válida no GeoJSON."}

    tree = STRtree(geoms_utm)
    return {
        "ok": True,
        "tree": tree,
        "geoms_utm": geoms_utm,
        "props": props_list,
        "ll_to_utm": ll_to_utm,
    }


def _nearest_street(lon: float, lat: float, radius_m: float) -> dict[str, Any]:
    idx = _streets_index()
    if not idx.get("ok"):
        return {"found": False, "reason": idx.get("reason", "Falha ao carregar ruas.")}

    tree: STRtree = idx["tree"]
    geoms_utm = idx["geoms_utm"]
    props_list = idx["props"]
    ll_to_utm = idx["ll_to_utm"]

    x, y = ll_to_utm(lon, lat)
    p = Point(x, y)

    try:
        g_near = tree.nearest(p)
        if g_near is None:
            return {"found": False, "reason": "Nenhuma via encontrada."}
        dist = float(p.distance(g_near))
    except Exception:
        return {"found": False, "reason": "Erro ao buscar via mais próxima."}

    if dist > float(radius_m):
        return {
            "found": False,
            "distance_m": dist,
            "reason": f"Via não encontrada no raio de {radius_m:.0f} m (mais próxima a {dist:.1f} m).",
        }

    try:
        i = geoms_utm.index(g_near)
    except ValueError:
        i = 0
        for j, g in enumerate(geoms_utm):
            if g.equals(g_near):
                i = j
                break

    props = props_list[i]
    name = (props.get("log_ofic") or props.get("nome") or props.get("name") or "").strip()
    road_type = (props.get("hierarquia") or props.get("tipo") or props.get("class") or "").strip()

    return {
        "found": True,
        "name": name or "Sem nome (cadastro)",
        "type": road_type or "Sem classificação (cadastro)",
        "distance_m": dist,
    }


def _log_query(payload: dict[str, Any]) -> None:
    """Grava log no Supabase em `query_logs` (se existir)."""
    try:
        sb = get_supabase()
        sb.table("query_logs").insert(payload).execute()
    except Exception as e:
        st.warning(f"Log (query_logs) não gravado: {e}")


def _render_map(zones_gj, lat0=-3.689, lon0=-40.349, click_lat=None, click_lon=None):
    m = folium.Map(location=[lat0, lon0], zoom_start=12, tiles="OpenStreetMap", control_scale=True)

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


st.set_page_config(layout="wide", page_title=APP_TITLE)
st.title(APP_TITLE)

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

zones = _zones()
zones_gj = zones["geojson"]

st.subheader("1) Selecione o ponto no mapa")
radius_m = st.number_input("Raio para encontrar via (m)", min_value=10, max_value=1000, value=100, step=10)

last_click = st.session_state.get("last_click")
click_lat = last_click.get("lat") if last_click else None
click_lon = last_click.get("lon") if last_click else None

m = _render_map(zones_gj, click_lat=click_lat, click_lon=click_lon)
out = st_folium(m, width=None, height=420)

lat = lon = None
zone = None

if out and out.get("last_clicked"):
    lat = float(out["last_clicked"]["lat"])
    lon = float(out["last_clicked"]["lng"])
    st.session_state.last_click = {"lat": lat, "lon": lon}

    zone = zone_from_latlon(zones["prepared"], lat, lon)
    if zone:
        st.success(f"Zona detectada: {zone}")
    else:
        st.warning("Clique fora das zonas. Tente outro ponto.")

st.divider()

st.subheader("2) Localização (zona + via)")

street_info = None
if lat is not None and lon is not None:
    street_info = _nearest_street(lon, lat, radius_m)

    colA, colB, colC = st.columns(3)
    with colA:
        st.write("**Zona**")
        st.write(zone or "—")
    with colB:
        st.write("**Rua / Logradouro**")
        st.write(street_info["name"] if street_info.get("found") else "Via não encontrada")
    with colC:
        st.write("**Tipo de via**")
        st.write(street_info["type"] if street_info.get("found") else "—")

    if street_info.get("found"):
        st.caption(f"Distância até o eixo da via: {street_info['distance_m']:.1f} m (raio {radius_m:.0f} m).")
    else:
        dist = street_info.get("distance_m")
        if dist is not None:
            st.warning(f"Via não encontrada no raio de {radius_m:.0f} m. Mais próxima a {dist:.1f} m. Tente aumentar o raio.")
        else:
            st.warning(f"Via não encontrada. Tente aumentar o raio para > {radius_m:.0f} m.")
else:
    st.info("Clique no mapa para identificar zona e via.")

st.divider()

st.subheader("3) Dados do lote")
col1, col2, col3 = st.columns(3)
with col1:
    lot_area = st.number_input("Área do lote (m²)", min_value=1.0, value=300.0, step=10.0)
with col2:
    testada = st.number_input("Largura (testada) (m)", min_value=1.0, value=10.0, step=0.5)
with col3:
    profundidade = st.number_input("Profundidade (m)", min_value=1.0, value=30.0, step=0.5)

built_ground = st.number_input("Área pretendida no térreo (m²)", min_value=0.0, value=0.0, step=5.0)

st.subheader("4) Regras (fonte única: Supabase)")
use_type_code = st.text_input("use_type_code", value="RES_UNI")

rule = None
if zone:
    try:
        rule = get_zone_rule(zone, use_type_code)
        if rule:
            st.json(rule, expanded=True)
        else:
            st.warning("Nenhuma regra encontrada para (zona + uso).")
    except Exception as e:
        st.error(f"Erro ao consultar Supabase: {e}")
else:
    st.info("Selecione uma zona no mapa para buscar regras no Supabase.")

st.subheader("5) Cálculos")
if rule:
    try:
        result = compute(
            lot_area_m2=float(lot_area),
            testada_m=float(testada),
            profundidade_m=float(profundidade),
            built_ground_m2=float(built_ground),
            to_max_pct=(rule.get("to_max_pct") or rule.get("to_max") or rule.get("to_sub_max")),
            tp_min_pct=(rule.get("tp_min_pct") or rule.get("tp_min")),
            ia_max=(rule.get("ia_max") or rule.get("ia") or rule.get("ia_maximo")),
            recuo_frontal_m=rule.get("recuo_frontal_m"),
            recuo_lateral_m=rule.get("recuo_lateral_m"),
            recuo_fundos_m=rule.get("recuo_fundos_m"),
            allow_attach_one_side=rule.get("allow_attach_one_side", False),
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("TO máx (m² no térreo)", f"{result['to_max_m2']:.2f}", f"{result['to_max_pct']:.2f}% do lote")
        with c2:
            st.metric("TP mín (m² permeável)", f"{result['tp_min_m2']:.2f}", f"{result['tp_min_pct']:.2f}% do lote")
        with c3:
            st.metric("IA máx (m² total)", f"{result['ia_max_m2']:.2f}", f"IA = {result['ia_max']:.2f}")

        st.markdown("---")
        st.markdown("### Opção 1 — Recuos padrão (zone_rules)")
        st.json(result["option_standard"], expanded=True)

        st.markdown("### Opção 2 — Art. 112 (zerar frontal/laterais; manter fundos)")
        st.json(result["option_art112"], expanded=True)

        st.markdown("---")
        st.markdown("### 6) Quadro técnico final (consolidado)")
        st.markdown(f"- Zona: **{zone}**")
        st.markdown(f"- Uso: **Residencial Unifamiliar ({use_type_code})**")
        st.markdown(f"- Área do lote: **{lot_area:.2f} m²**")
        st.markdown(f"- TO máx: **{result['to_max_pct']:.2f}%** (≈ **{result['to_max_m2']:.2f} m²** no térreo)")
        st.markdown(f"- TP mín: **{result['tp_min_pct']:.2f}%** (≈ **{result['tp_min_m2']:.2f} m²** permeável)")
        st.markdown(f"- IA máx: **{result['ia_max']:.2f}** (≈ **{result['ia_max_m2']:.2f} m²** total)")
        st.markdown(
            f"- Recuos (padrão): frontal **{(rule.get('recuo_frontal_m') or 0):.2f} m** | "
            f"lateral **{(rule.get('recuo_lateral_m') or 0):.2f} m** | "
            f"fundos **{(rule.get('recuo_fundos_m') or 0):.2f} m**"
        )
        st.markdown(f"- Máx. térreo (padrão): **{result['option_standard']['Máximo no térreo (respeitando TO e recuos) (m²)']:.2f} m²**")
        st.markdown(f"- Máx. térreo (Art.112): **{result['option_art112']['Máximo no térreo (Art.112, respeitando TO) (m²)']:.2f} m²**")

        # Log no Supabase (opcional)
        if lat is not None and lon is not None:
            street_name = street_info.get("name") if street_info else None
            street_type = street_info.get("type") if street_info else None
            street_dist = street_info.get("distance_m") if street_info else None

            _log_query(
                {
                    "session_id": st.session_state.session_id,
                    "app_version": APP_VERSION,
                    "clicked_lat": lat,
                    "clicked_lon": lon,
                    "zone_sigla": zone,
                    "use_type_code": use_type_code,
                    "street_name": street_name,
                    "street_type": street_type,
                    "street_distance_m": street_dist,
                    "radius_m": float(radius_m),
                }
            )

    except Exception as e:
        st.error(f"Erro nos cálculos: {e}")
else:
    st.info("Preencha (zona + regras) para calcular.")
