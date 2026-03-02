from __future__ import annotations

import streamlit as st

from core.zones_map import zone_from_latlon
from core.streets import find_street
from core.zone_rules_repository import get_zone_rule


def render_localizacao_section(*, calcular: bool, zones_prepared, radius_m: int):
    """Renderiza o bloco 3) Localização (zona + via), sem alterar layout.

    - Mantém o input de use_type_code
    - Só roda a busca quando clicar em 'Calcular viabilidade'
    - Atualiza st.session_state.calc (zona, rua, regra, erros)
    - Renderiza as 3 colunas (Zona/Rua/Tipo) + distância + warning
    """
    st.subheader("3) Localização (zona + via)")

    use_type_code = st.text_input(
        "use_type_code",
        value=st.session_state.calc.get("use_type_code") or "RES_UNI",
    )

    if calcular and st.session_state.last_click:
        lat = st.session_state.last_click["lat"]
        lon = st.session_state.last_click["lon"]

        st.session_state.calc["lat"] = lat
        st.session_state.calc["lon"] = lon
        st.session_state.calc["use_type_code"] = use_type_code
        st.session_state.calc["radius_m"] = int(radius_m)

        zone = zone_from_latlon(zones_prepared, lat, lon)
        street_info = find_street(lat=lat, lon=lon, radius_m=float(radius_m))

        st.session_state.calc["zone"] = zone
        st.session_state.calc["street_info"] = street_info

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

    calc = st.session_state.calc
    zone = calc.get("zone")
    street_info = calc.get("street_info")

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
