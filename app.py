from __future__ import annotations

from pathlib import Path

import folium
import streamlit as st
from streamlit_folium import st_folium

from core.zone_rules_repository import get_zone_rule
from core.zones_map import load_zones, zone_from_latlon
from core.calculations import compute

from core.streets import load_streets_index, nearest_street_from_latlon


APP_TITLE = "Viabilidade Sobral – Residencial Unifamiliar (v1.1)"
DATA_DIR = Path(__file__).parent / "data"
ZONE_FILE = DATA_DIR / "zoneamento_light.json"
RUAS_FILE = DATA_DIR / "ruas.json"


@st.cache_resource(show_spinner=False)
def _zones():
    return load_zones(ZONE_FILE)


@st.cache_resource(show_spinner=False)
def _streets():
    # Se não existir, o app continua sem travar (só não mostra rua)
    if not RUAS_FILE.exists():
        return None
    return load_streets_index(RUAS_FILE)


def _render_map(zones) -> tuple[float | None, float | None, str | None]:
    """Mapa de seleção obrigatória de zona + PIN no clique."""
    st.subheader("1) Selecionar localização (clique no mapa)")

    # default view (Sobral)
    center = (-3.6842, -40.3160)

    m = folium.Map(location=center, zoom_start=12, control_scale=True)

    # desenha zonas (simplificado)
    for feat in zones["features"]:
        folium.GeoJson(
            feat,
            name="Zonas",
            style_function=lambda _x: {
                "fillColor": "#1E88E5",
                "color": "#1E88E5",
                "weight": 1,
                "fillOpacity": 0.15,
            },
        ).add_to(m)

    # Se já existe um ponto salvo, coloca um PIN
    pin_lat = st.session_state.get("pin_lat")
    pin_lon = st.session_state.get("pin_lon")
    pin_zone = st.session_state.get("pin_zone")

    if pin_lat is not None and pin_lon is not None:
        popup_txt = f"Local escolhido<br>lat: {pin_lat:.6f}<br>lon: {pin_lon:.6f}"
        if pin_zone:
            popup_txt += f"<br><b>Zona:</b> {pin_zone}"
        folium.Marker(
            location=(pin_lat, pin_lon),
            popup=folium.Popup(popup_txt, max_width=300),
            tooltip="Ponto selecionado",
            icon=folium.Icon(color="red", icon="map-marker"),
        ).add_to(m)

    out = st_folium(m, height=380, width=None)

    last_clicked = out.get("last_clicked") if isinstance(out, dict) else None
    if last_clicked:
        lat = float(last_clicked["lat"])
        lon = float(last_clicked["lng"])
        zone = zone_from_latlon(zones, lat, lon)

        st.session_state["pin_lat"] = lat
        st.session_state["pin_lon"] = lon
        st.session_state["pin_zone"] = zone

        # força re-render para o PIN aparecer imediatamente
        st.rerun()

    # retorno atual (se não clicou agora, devolve o que já tinha)
    lat = st.session_state.get("pin_lat")
    lon = st.session_state.get("pin_lon")
    zone = st.session_state.get("pin_zone")
    return lat, lon, zone


def main():
    st.set_page_config(layout="wide", page_title="Viabilidade")
    st.title(APP_TITLE)

    zones = _zones()
    streets_index = _streets()

    lat, lon, zone = _render_map(zones)

    if not lat or not lon:
        st.warning("Clique no mapa para selecionar o local.")
        st.stop()

    # Mostrar zona + rua/tipo (se achar)
    st.success(f"Zona detectada: {zone}")
    st.caption(f"Clique: lat {lat:.6f}, lon {lon:.6f}")

    street_hit = None
    if streets_index is not None:
        street_hit = nearest_street_from_latlon(streets_index, lat, lon, max_distance_m=80.0)

    if street_hit:
        st.info(
            f"**Rua:** {street_hit.name}  \n"
            f"**Tipo de via:** {street_hit.hierarchy}  \n"
            f"**Distância aproximada:** {street_hit.distance_m:.1f} m"
        )
    else:
        st.info("Rua/tipo de via: não encontrado (ou dataset de ruas não carregado).")

    st.subheader("2) Dados do lote")

    col1, col2, col3 = st.columns(3)
    with col1:
        area_lote = st.number_input("Área do lote (m²)", min_value=1.0, value=300.0, step=1.0, format="%.2f")
    with col2:
        testada = st.number_input("Largura (testada) (m)", min_value=1.0, value=10.0, step=0.5, format="%.2f")
    with col3:
        profundidade = st.number_input("Profundidade (m)", min_value=1.0, value=30.0, step=0.5, format="%.2f")

    area_terreo = st.number_input(
        "Área pretendida no térreo (m²)",
        min_value=0.0,
        value=0.0,
        step=1.0,
        format="%.2f",
    )

    st.subheader("3) Regras (fonte única: Supabase)")

    # Exemplo fixo de uso (você pode trocar depois para dropdown)
    use_type_code = "RES_UNI"

    try:
        rule = get_zone_rule(zone_sigla=zone, use_type_code=use_type_code)
        st.json(rule)
    except Exception as e:
        st.error(f"Erro ao consultar Supabase: {e}")
        st.stop()

    st.subheader("4) Cálculos")
    result = compute(
        area_lote_m2=area_lote,
        testada_m=testada,
        profundidade_m=profundidade,
        area_terreo_pretendida_m2=area_terreo,
        rule=rule,
    )

    cols = st.columns(3)
    with cols[0]:
        st.metric("TO máx (m² no térreo)", f"{result.to_max_m2:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.caption(f"{result.to_max_pct:.2f}% do lote")
    with cols[1]:
        st.metric("TP mín (m² permeável)", f"{result.tp_min_m2:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.caption(f"{result.tp_min_pct:.2f}% do lote")
    with cols[2]:
        st.metric("IA máx (m² total)", f"{result.ia_max_m2:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.caption(f"IA = {result.ia_max:.2f}")

    st.markdown("---")
    st.subheader("5) Quadro técnico final (consolidado)")
    st.markdown(
        f"""
- **Zona:** {zone}
- **Uso:** Residencial Unifamiliar ({use_type_code})
- **Área do lote:** {area_lote:,.2f} m²
- **TO máx:** {result.to_max_pct:.2f}% (≈ {result.to_max_m2:,.2f} m² no térreo)
- **TP mín:** {result.tp_min_pct:.2f}% (≈ {result.tp_min_m2:,.2f} m² permeável)
- **IA máx:** {result.ia_max:.2f} (≈ {result.ia_max_m2:,.2f} m² total)
"""
    )


if __name__ == "__main__":
    main()
