from __future__ import annotations

import streamlit as st

from core.zones_map import zone_from_latlon
from core.streets import find_street


def _sync_street_fields(calc: dict) -> None:
    """Normaliza/achata street_info para chaves estáveis usadas por índices/análise/relatório."""
    si = calc.get("street_info") if isinstance(calc, dict) else None
    if not isinstance(si, dict):
        return
    name = si.get("name")
    typ = si.get("type")
    dist = si.get("distance_m")
    calc["street_name"] = name
    calc["street_type"] = typ
    calc["street_dist"] = dist
    # novos aliases (mantém compat com handoff)
    calc["via_nome"] = calc.get("via_nome") or name
    calc["via_tipo"] = calc.get("via_tipo") or typ
    calc["via_dist_m"] = calc.get("via_dist_m") or dist


def render_localizacao_section(*args, **kwargs):
    """Renderiza o bloco 3) Localização (zona + via), sem alterar layout.

    Compatibilidade:
    - Novo (clean): render_localizacao_section(calcular=..., zones_prepared=..., radius_m=...)
    - Antigo (MVP): render_localizacao_section((lat, lon), radius_m=...)

    Regras do contrato:
    - Não muda nomes de chaves no calc
    - Só calcula quando clicar no botão do app (calcular=True)
    - Não consulta Supabase aqui (regra é responsabilidade do app/indices)
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

    # Novo estilo (kwargs)
    calcular = bool(kwargs.get("calcular", False))
    zones_prepared = kwargs.get("zones_prepared")
    radius_m = int(kwargs.get("radius_m", 150))

    st.subheader("3) Localização (zona + via)")

    use_type_code = st.text_input(
        "use_type_code",
        value=st.session_state.calc.get("use_type_code") or "RES_UNI",
    )

    # Executa somente quando clicar no botão
    if calcular:
        if not st.session_state.get("last_click"):
            st.session_state.calc["ok"] = False
            st.session_state.calc["err"] = "Clique no mapa para selecionar um ponto."
        else:
            lat = float(st.session_state.last_click["lat"])
            lon = float(st.session_state.last_click["lon"])

            calc = st.session_state.calc
            calc["lat"] = lat
            calc["lon"] = lon
            calc["use_type_code"] = use_type_code
            calc["radius_m"] = int(radius_m)

            # zona + via
            zone = zone_from_latlon(zones_prepared, lat, lon)
            street_info = find_street(lat=lat, lon=lon, radius_m=float(radius_m))

            calc["zone"] = zone
            calc["zone_sigla"] = zone  # alias compat (relatório antigo)
            calc["street_info"] = street_info

            # achata
            _sync_street_fields(calc)

            # OK only if zone exists; street can be None (não derruba)
            if not zone:
                calc["ok"] = False
                calc["err"] = "Ponto fora das zonas (zoneamento_light.json)."
            else:
                # não zera erro se já existir algo do Supabase; só limpa erro de localização
                if calc.get("err") in (None, "") or "Ponto fora" in str(calc.get("err")):
                    calc["err"] = None
                calc["ok"] = True

    # Render (estado atual)
    calc = st.session_state.calc
    zone = calc.get("zone")
    street_info = calc.get("street_info") if isinstance(calc.get("street_info"), dict) else None

    colA, colB, colC = st.columns(3)
    with colA:
        st.write("Zona")
        st.write(zone or "—")
    with colB:
        st.write("Rua / Logradouro")
        st.write((street_info.get("name") if street_info else None) or "—")
    with colC:
        st.write("Tipo de via")
        st.write((street_info.get("type") if street_info else None) or "—")

    if street_info and street_info.get("distance_m") is not None:
        st.caption(
            f"Distância até o eixo da via: {float(street_info['distance_m']):.1f} m "
            f"(raio {float(calc.get('radius_m') or radius_m):.0f} m)."
        )

    if calc.get("err"):
        st.warning(str(calc["err"]))
