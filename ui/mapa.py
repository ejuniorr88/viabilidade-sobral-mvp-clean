from __future__ import annotations

import streamlit as st
import folium
from streamlit_folium import st_folium


def _safe_prop(feature, key, default=""):
    try:
        return ((feature or {}).get("properties") or {}).get(key, default)
    except Exception:
        return default


def _zone_style(feature):
    sigla = str(_safe_prop(feature, "sigla", "") or "").upper().strip()
    subzona = str(_safe_prop(feature, "subzona", "") or "").upper().strip()
    zona_sigla = str(_safe_prop(feature, "zona_sigla", "") or "").upper().strip()
    zeia_text = " ".join([sigla, subzona, zona_sigla]).upper()

    style = {
        "fillOpacity": 0.08,
        "weight": 1,
        "color": "#3388ff",
    }

    # Destaque visual das ZEIA para auditoria do clique.
    if sigla == "ZEIA" or "ZEIA" in zeia_text:
        style.update({"fillOpacity": 0.18, "weight": 2})
        if "APP" in zeia_text:
            style.update({"color": "#d62728"})
        elif "3" in zeia_text:
            style.update({"color": "#9467bd"})
        elif "2" in zeia_text:
            style.update({"color": "#ff7f0e"})
        elif "1" in zeia_text:
            style.update({"color": "#2ca02c"})
        else:
            style.update({"color": "#17becf"})

    return style


def _render_map(zones_gj, lat0=-3.689, lon0=-40.349, click_lat=None, click_lon=None):
    """Renderiza mapa Folium + GeoJson de zonas e marcador do clique."""
    m = folium.Map(
        location=[lat0, lon0],
        zoom_start=12,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    if zones_gj:
        folium.GeoJson(
            zones_gj,
            name="Zonas",
            style_function=_zone_style,
            highlight_function=lambda _: {"weight": 4, "fillOpacity": 0.28},
            tooltip=folium.GeoJsonTooltip(
                fields=["sigla", "subzona", "zona_sigla"],
                aliases=["Sigla", "Subzona", "Zona"],
                localize=True,
                sticky=False,
                labels=True,
            ),
        ).add_to(m)

    if click_lat is not None and click_lon is not None:
        folium.Marker(
            location=[click_lat, click_lon],
            tooltip="Ponto selecionado",
        ).add_to(m)

    folium.LayerControl(collapsed=True).add_to(m)
    return m


def render_mapa_section(
    zones_gj,
    *,
    state_key_last_click: str = "last_click",
    state_key_click_hash: str = "click_hash",
    state_key_calc: str = "calc",
    default_radius_m: int = 100,
) -> int:
    """Seção 1) Mapa + raio.

    - Atualiza st.session_state[last_click] e st.session_state[click_hash]
    - Quando o clique muda, marca calc['ok']=False e calc['err']=None
    - Retorna o radius_m (int)
    """
    st.subheader("1) Selecione o ponto no mapa")
    st.caption(
        "Auditoria visual ZEIA: APP em vermelho, ZEIA 1 em verde, ZEIA 2 em laranja, "
        "ZEIA 3 em roxo e ZEIA genérica em azul-claro. Passe o mouse para ver sigla/subzona."
    )

    # raio (int) — Streamlit não aceita misturar int/float no number_input
    radius_m = st.number_input(
        "Raio para encontrar via (m)",
        min_value=10,
        max_value=100000,
        value=int((st.session_state.get(state_key_calc, {}) or {}).get("radius_m") or default_radius_m),
        step=10,
    )

    last_click = st.session_state.get(state_key_last_click)
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

        if new_hash != st.session_state.get(state_key_click_hash):
            st.session_state[state_key_last_click] = {"lat": new_lat, "lon": new_lon}
            st.session_state[state_key_click_hash] = new_hash

            # when click changes, mark results as not calculated yet
            calc = st.session_state.get(state_key_calc) or {}
            if isinstance(calc, dict):
                calc["ok"] = False
                calc["err"] = None
                # guarda o radius para manter consistência com o resto do app
                calc["radius_m"] = int(radius_m)

                # IMPORTANT: quando o clique muda, limpamos resultados dependentes do ponto,
                # para evitar "zona travada" / regra antiga em novo ponto.
                calc["zone"] = None
                calc["zone_sigla"] = None
                calc["via_nome"] = None
                calc["via_tipo"] = None
                calc["via_dist_m"] = None
                calc["street_name"] = None
                calc["street_type"] = None
                calc["street_dist"] = None

                # regra + cálculos
                calc["rule"] = None
                calc["basic"] = None
                calc["ia_utilizado"] = None
                calc["to_utilizada_pct"] = None
                calc["tp_prevista_pct"] = None

                # guarda o hash do clique para forçar recálculo no item 3
                calc["_click_hash"] = new_hash

                st.session_state[state_key_calc] = calc

            st.rerun()

    # show coordinates caption
    if st.session_state.get(state_key_last_click):
        st.caption(
            f"📍 Coordenadas selecionadas: "
            f"lat {st.session_state[state_key_last_click]['lat']:.6f} | "
            f"lon {st.session_state[state_key_last_click]['lon']:.6f}"
        )

    return int(radius_m)
