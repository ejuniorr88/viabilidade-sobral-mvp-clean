from __future__ import annotations

import streamlit as st

# Compat: alguns branches renomearam módulos
try:
    from core.zones_map import zone_from_latlon
except Exception:  # pragma: no cover
    from core.zones_mapa import zone_from_latlon  # type: ignore

from core.streets import find_street


def render_localizacao_section(*args, **kwargs):
    """Renderiza o bloco 3) Localização (zona + via), sem alterar layout.

    Compatibilidade:
    - **Novo (clean):** render_localizacao_section(calcular=..., zones_prepared=..., radius_m=...)
    - **Chamado pelo app.py atual:** render_localizacao_section(calcular, zones_prepared, radius_m)
    - **Antigo (MVP):** render_localizacao_section((lat, lon), radius_m=...)

    Regras importantes:
    - Só roda a busca quando clicar em 'Calcular viabilidade'
    - Atualiza st.session_state.calc com chaves "novas" e aliases "antigas" (para relatório)
    - NÃO consulta regra do Supabase aqui (para não bloquear o fetch do app.py)
    """

    # ----------------------------
    # Compat: chamada antiga com (lat, lon)
    # ----------------------------
    if args and len(args) >= 1 and isinstance(args[0], (tuple, list)) and len(args[0]) == 2:
        lat = float(args[0][0])
        lon = float(args[0][1])
        radius_m = int(kwargs.get("radius_m", 150))

        st.subheader("3) Localização (zona + via)")
        street_info = find_street(lat=lat, lon=lon, radius_m=float(radius_m))

        if street_info and "distance_m" in street_info:
            st.caption(
                f"Distância até o eixo da via: {float(street_info['distance_m']):.1f} m (raio {radius_m} m)."
            )
        if street_info:
            st.success(f"Rua mais próxima: {street_info.get('name','')} ({street_info.get('type','')})")
        else:
            st.warning("Não foi possível identificar a rua mais próxima.")
        return street_info

    # ----------------------------
    # Novo estilo (kwargs OU posicional)
    # ----------------------------
    # app.py atual chama assim:
    #   render_localizacao_section(calcular, zones_prepared, radius_m)
    if args and len(args) >= 1 and isinstance(args[0], (bool, int)):
        calcular = bool(args[0])
        zones_prepared = args[1] if len(args) >= 2 else kwargs.get("zones_prepared")
        radius_m = int(args[2]) if len(args) >= 3 else int(kwargs.get("radius_m", 150))
    else:
        calcular = bool(kwargs.get("calcular", False))
        zones_prepared = kwargs.get("zones_prepared")
        radius_m = int(kwargs.get("radius_m", 150))

    st.subheader("3) Localização (zona + via)")

    # garante calc
    if "calc" not in st.session_state or not isinstance(st.session_state.calc, dict):
        st.session_state.calc = {}

    use_type_code = st.text_input(
        "use_type_code",
        value=st.session_state.calc.get("use_type_code") or "RES_UNI",
    )

    if calcular and st.session_state.get("last_click"):
        lat = float(st.session_state.last_click["lat"])
        lon = float(st.session_state.last_click["lon"])

        st.session_state.calc["lat"] = lat
        st.session_state.calc["lon"] = lon
        st.session_state.calc["use_type_code"] = use_type_code
        st.session_state.calc["radius_m"] = int(radius_m)

        zone = zone_from_latlon(zones_prepared, lat, lon)
        street_info = find_street(lat=lat, lon=lon, radius_m=float(radius_m))

        # contrato principal
        st.session_state.calc["zone"] = zone
        st.session_state.calc["street_info"] = street_info

        # aliases p/ relatório (compat)
        st.session_state.calc["zone_sigla"] = zone

        if street_info:
            st.session_state.calc["street_name"] = street_info.get("name")
            st.session_state.calc["street_type"] = street_info.get("type")
            st.session_state.calc["street_dist"] = street_info.get("distance_m")

            # chaves novas também
            st.session_state.calc["via_nome"] = street_info.get("name")
            st.session_state.calc["via_tipo"] = street_info.get("type")
            st.session_state.calc["via_dist_m"] = street_info.get("distance_m")
        else:
            st.session_state.calc["street_name"] = None
            st.session_state.calc["street_type"] = None
            st.session_state.calc["street_dist"] = None
            st.session_state.calc["via_nome"] = None
            st.session_state.calc["via_tipo"] = None
            st.session_state.calc["via_dist_m"] = None

        # Não consulta regra aqui; deixa o app.py fazer fetch_rule()
        st.session_state.calc.setdefault("rule", None)

        # status
        if zone:
            st.session_state.calc["err"] = None
            st.session_state.calc["ok"] = True
        else:
            st.session_state.calc["err"] = "Clique fora das zonas."
            st.session_state.calc["ok"] = False

    calc = st.session_state.calc
    zone = calc.get("zone")
    street_info = calc.get("street_info")

    colA, colB, colC = st.columns(3)
    with colA:
        st.write("Zona")
        st.write(zone or "—")
    with colB:
        st.write("Rua / Logradouro")
        st.write(street_info.get("name") if isinstance(street_info, dict) else "—")
    with colC:
        st.write("Tipo de via")
        st.write(street_info.get("type") if isinstance(street_info, dict) else "—")

    if isinstance(street_info, dict) and "distance_m" in street_info:
        st.caption(
            f"Distância até o eixo da via: {float(street_info['distance_m']):.1f} m "
            f"(raio {float(calc.get('radius_m') or radius_m):.0f} m)."
        )

    if calc.get("err"):
        st.warning(str(calc["err"]))
