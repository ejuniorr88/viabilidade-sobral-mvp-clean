from __future__ import annotations

from pathlib import Path

import folium
import streamlit as st
from streamlit_folium import st_folium

from core.zone_rules_repository import get_zone_rule
from core.zones_map import load_zones, zone_from_latlon
from core.calculations import compute


APP_TITLE = "Viabilidade Sobral — Residencial Unifamiliar (v1.1)"
DATA_DIR = Path(__file__).parent / "data"
ZONE_FILE = DATA_DIR / "zoneamento_light.json"


@st.cache_resource(show_spinner=False)
def _zones():
    return load_zones(ZONE_FILE)


def _render_map() -> tuple[float | None, float | None, str | None]:
    """Mapa de seleção obrigatória de zona.

    - Usuário clica no mapa
    - Detectamos zona pelo GeoJSON
    - Retornamos (lat, lon, zone_sigla)
    """

    st.subheader("1) Clique no mapa para detectar a zona")

    # Centro aproximado de Sobral
    m = folium.Map(location=[-3.689, -40.349], zoom_start=13, control_scale=True)

    # Adiciona camada das zonas (visual)
    folium.GeoJson(
        data=str(ZONE_FILE),
        name="Zoneamento",
        tooltip=folium.GeoJsonTooltip(fields=["sigla"], aliases=["Zona:"] , sticky=False),
    ).add_to(m)
    folium.LayerControl().add_to(m)

    out = st_folium(m, height=520, use_container_width=True)

    lat = lon = None
    sigla = None

    if out and out.get("last_clicked"):
        lat = out["last_clicked"].get("lat")
        lon = out["last_clicked"].get("lng")
        if lat is not None and lon is not None:
            sigla = zone_from_latlon(_zones(), lat=float(lat), lon=float(lon))

    return lat, lon, sigla


def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)

    # --- MAPA (zona obrigatória) ---
    lat, lon, zone_sigla = _render_map()

    if zone_sigla:
        st.success(f"Zona detectada: **{zone_sigla}**")
        st.caption(f"Clique: lat {lat:.6f}, lon {lon:.6f}")
        st.session_state["zone_sigla"] = zone_sigla
    else:
        # Mantém zona anterior se o usuário já clicou antes
        zone_sigla = st.session_state.get("zone_sigla")
        if zone_sigla:
            st.info(f"Zona atual (último clique válido): **{zone_sigla}**")
        else:
            st.warning("Clique no mapa para detectar a zona (não há seleção manual).")

    st.divider()

    st.subheader("2) Dados do lote")
    c1, c2, c3 = st.columns(3)
    with c1:
        lot_area = st.number_input("Área do lote (m²)", min_value=1.0, value=300.0, step=1.0)
    with c2:
        lot_width = st.number_input("Largura (testada) (m)", min_value=1.0, value=10.0, step=0.5)
    with c3:
        lot_depth = st.number_input("Profundidade (m)", min_value=1.0, value=30.0, step=0.5)

    area_terreo = st.number_input("Área pretendida no térreo (m²)", min_value=0.0, value=0.0, step=1.0)

    USE_TYPE_CODE = "RES_UNI"  # Residencial unifamiliar

    st.divider()
    st.subheader("3) Regras (fonte única: Supabase)")

    if not zone_sigla:
        st.stop()

    try:
        rule = get_zone_rule(zone_sigla, USE_TYPE_CODE)
    except Exception as e:
        st.error(f"Erro ao consultar Supabase: {e}")
        st.stop()

    if rule is None:
        st.error(f"Sem regra cadastrada no Supabase para **{zone_sigla} + {USE_TYPE_CODE}**.")
        st.stop()

    st.write(
        {
            "zone_sigla": rule.zone_sigla,
            "use_type_code": rule.use_type_code,
            "to_max_pct": rule.to_max_pct,
            "tp_min_pct": rule.tp_min_pct,
            "ia_max": rule.ia_max,
            "recuo_frontal_m": rule.recuo_frontal_m,
            "recuo_lateral_m": rule.recuo_lateral_m,
            "recuo_fundos_m": rule.recuo_fundos_m,
        }
    )

    st.divider()
    st.subheader("4) Cálculos")

    calc = compute(
        lot_area_m2=lot_area,
        lot_width_m=lot_width,
        lot_depth_m=lot_depth,
        to_max_pct=rule.to_max_pct,
        tp_min_pct=rule.tp_min_pct,
        ia_max=rule.ia_max,
        recuo_frontal_m=rule.recuo_frontal_m,
        recuo_lateral_m=rule.recuo_lateral_m,
        recuo_fundos_m=rule.recuo_fundos_m,
    )

    # Status simples
    ok_to = area_terreo <= calc.to_max_area + 1e-9

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("TO máx (m² no térreo)", f"{calc.to_max_area:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.caption(f"{rule.to_max_pct:.2f}% do lote")
    with c2:
        st.metric("TP mín (m² permeável)", f"{calc.tp_min_area:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.caption(f"{rule.tp_min_pct:.2f}% do lote")
    with c3:
        st.metric("IA máx (m² total)", f"{calc.ia_max_area_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.caption(f"IA = {rule.ia_max:.2f}")

    st.markdown("### Opção 1 — Recuos padrão (zone_rules)")
    st.write(
        {
            "Área interna disponível (miolo) (m²)": round(calc.buildable_area_standard, 2),
            "Máximo no térreo (respeitando TO e recuos) (m²)": round(calc.max_terreo_standard, 2),
        }
    )

    st.markdown("### Opção 2 — Art. 112 (zerar frontal/laterais; manter fundos)")
    st.write(
        {
            "Área interna disponível (Art.112) (m²)": round(calc.buildable_area_art112, 2),
            "Máximo no térreo (Art.112, respeitando TO) (m²)": round(calc.max_terreo_art112, 2),
        }
    )

    st.divider()
    st.subheader("5) Quadro técnico final (consolidado)")

    st.markdown(
        "\n".join(
            [
                f"- **Zona:** {zone_sigla}",
                f"- **Uso:** Residencial Unifamiliar (RES_UNI)",
                f"- **Área do lote:** {lot_area:,.2f} m²".replace(",", "X").replace(".", ",").replace("X", "."),
                f"- **TO máx:** {rule.to_max_pct:.2f}% (≈ {calc.to_max_area:,.2f} m² no térreo)".replace(",", "X").replace(".", ",").replace("X", "."),
                f"- **TP mín:** {rule.tp_min_pct:.2f}% (≈ {calc.tp_min_area:,.2f} m² permeável)".replace(",", "X").replace(".", ",").replace("X", "."),
                f"- **IA máx:** {rule.ia_max:.2f} (≈ {calc.ia_max_area_total:,.2f} m² total)".replace(",", "X").replace(".", ",").replace("X", "."),
                f"- **Recuos (padrão):** frontal {rule.recuo_frontal_m:.2f} m | lateral {rule.recuo_lateral_m:.2f} m | fundos {rule.recuo_fundos_m:.2f} m",
                f"- **Máx. térreo (padrão):** {calc.max_terreo_standard:,.2f} m²".replace(",", "X").replace(".", ",").replace("X", "."),
                f"- **Máx. térreo (Art.112):** {calc.max_terreo_art112:,.2f} m²".replace(",", "X").replace(".", ",").replace("X", "."),
                "- **Vagas (Anexo IV):** Não exigido (Residencial Unifamiliar)",
            ]
        )
    )

    if area_terreo > 0:
        st.divider()
        st.subheader("Checagem rápida")
        if ok_to:
            st.success("A área pretendida no térreo está dentro do limite de TO (antes de considerar recuos).")
        else:
            st.error("A área pretendida no térreo ultrapassa o limite de TO.")


if __name__ == "__main__":
    main()
