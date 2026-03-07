from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import streamlit as st

try:
    from core.zones_map import zone_from_latlon
except Exception:
    from core.zones_mapa import zone_from_latlon  # type: ignore

from core.streets import find_street

# ZEIP sectors (subzone_code)
try:
    from core.zeip_sectors import zeip_sector_from_latlon
except Exception:
    zeip_sector_from_latlon = None  # type: ignore


def _coerce_call(args, kwargs) -> Tuple[bool, Any, int]:
    """Compatibilidade com app.py: render_localizacao_section(calcular, zones_prepared, radius_m)."""
    if len(args) >= 3 and isinstance(args[0], (bool, int)):
        return bool(args[0]), args[1], int(args[2])
    return bool(kwargs.get("calcular", False)), kwargs.get("zones_prepared"), int(kwargs.get("radius_m", 150))


def render_localizacao_section(*args, **kwargs) -> Optional[Dict[str, Any]]:
    st.subheader("3) Localização (zona + via)")

    calcular, zones_prepared, radius_m = _coerce_call(args, kwargs)

    use_type_code = st.text_input(
        "use_type_code",
        value=st.session_state.calc.get("use_type_code") or "RES_UNI",
        key="use_type_code_input",
    )

    calc = st.session_state.calc

    if calcular:
        if not getattr(st.session_state, "last_click", None):
            calc["ok"] = False
            calc["err"] = "Clique no mapa para definir o ponto."
        else:
            lat = st.session_state.last_click["lat"]
            lon = st.session_state.last_click["lon"]

            calc["lat"] = lat
            calc["lon"] = lon
            calc["use_type_code"] = use_type_code
            calc["radius_m"] = int(radius_m)

            zone = zone_from_latlon(zones_prepared, lat, lon) if zones_prepared else None
            street_info = find_street(lat=lat, lon=lon, radius_m=float(radius_m))

            calc["zone"] = zone
            calc["zone_sigla"] = zone

            # ZEIS setores (ZEIS 1/2/3) — como o zoneamento_light.json marca apenas "ZEIS",
            # usamos um seletor simples para escolher o setor quando necessário.
            # Isso permite consultar regras/adequabilidade diferentes por ZEIS 1/2/3 no Supabase.
            if zone == "ZEIS":
                prev_zeis = calc.get("zeis_sigla") or calc.get("zone") or "ZEIS 1"
                # normaliza valores possíveis
                if str(prev_zeis).strip().upper() in ("ZEIS",):
                    prev_zeis = "ZEIS 1"
                calc["zeis_sigla"] = str(prev_zeis).strip().upper()
                # já atualiza a zona usada nas consultas
                calc["zone"] = calc["zeis_sigla"]
                calc["zone_sigla"] = calc["zeis_sigla"]

            if street_info:
                calc["via_nome"] = street_info.get("name")
                calc["via_tipo"] = street_info.get("type")
                calc["via_dist_m"] = street_info.get("distance_m")
                calc["street_name"] = street_info.get("name")
                calc["street_type"] = street_info.get("type")
                calc["street_dist"] = street_info.get("distance_m")
            else:
                calc["via_nome"] = None
                calc["via_tipo"] = None
                calc["via_dist_m"] = None
                calc["street_name"] = None
                calc["street_type"] = None
                calc["street_dist"] = None

            # Subzona / Setor ZEIP
            prev_sub = calc.get("subzone_code") or "PADRAO"
            subzone = "PADRAO"
            if zone == "ZEIP" and zeip_sector_from_latlon:
                try:
                    subzone = zeip_sector_from_latlon(lat, lon) or "PADRAO"
                except Exception:
                    subzone = "PADRAO"
            calc["subzone_code"] = subzone

            # Se o setor mudou, forçar recarregar regra/cálculos (evita ficar preso em PADRAO)
            if zone == "ZEIP" and subzone != prev_sub:
                calc.pop("rule", None)
                calc["basic"] = None
                calc["ia_utilizado"] = None
                calc["to_utilizada_pct"] = None
                calc["tp_prevista_pct"] = None

            if not zone:
                calc["ok"] = False
                calc["err"] = "Clique dentro de uma zona."
            else:
                calc["ok"] = True
                calc["err"] = None

    zone = calc.get("zone") or calc.get("zone_sigla")
    via_nome = calc.get("via_nome") or calc.get("street_name")
    via_tipo = calc.get("via_tipo") or calc.get("street_type")

    colA, colB, colC = st.columns(3)
    with colA:
        st.write("Zona")
        st.write(zone or "—")
    with colB:
        st.write("Rua / Logradouro")
        st.write(via_nome or "—")
    with colC:
        st.write("Tipo de via")
        st.write(via_tipo or "—")

    # Mostrar setor ZEIP (sem alterar layout)
    if zone == "ZEIP":
        st.caption(f"Setor ZEIP: {calc.get('subzone_code','PADRAO')}")

    # Mostrar/selecionar setor ZEIS (ZEIS 1/2/3) — sem alterar ordem das seções
    if zone and str(zone).strip().upper() == "ZEIS":
        # se ainda está "ZEIS" genérico, sugere ZEIS 1 por padrão
        current = (calc.get("zeis_sigla") or "ZEIS 1").strip().upper()
        if current == "ZEIS":
            current = "ZEIS 1"
        options = ["ZEIS 1", "ZEIS 2", "ZEIS 3"]
        try:
            idx = options.index(current)
        except ValueError:
            idx = 0
        zeis_pick = st.selectbox("Setor ZEIS", options, index=idx, key="zeis_setor_select")
        zeis_pick = str(zeis_pick).strip().upper()
        prev = calc.get("zeis_sigla") or ""
        calc["zeis_sigla"] = zeis_pick
        calc["zone"] = zeis_pick
        calc["zone_sigla"] = zeis_pick

        # se mudou, limpar regra/cálculos para refetch correto
        if prev and str(prev).strip().upper() != zeis_pick:
            calc.pop("rule", None)
            calc["basic"] = None
            calc["ia_utilizado"] = None
            calc["to_utilizada_pct"] = None
            calc["tp_prevista_pct"] = None

    dist = calc.get("via_dist_m") if calc.get("via_dist_m") is not None else calc.get("street_dist")
    if dist is not None:
        try:
            st.caption(
                f"Distância até o eixo da via: {float(dist):.1f} m (raio {float(calc.get('radius_m') or radius_m):.0f} m)."
            )
        except Exception:
            pass

    if calc.get("err"):
        st.warning(str(calc["err"]))

    return {"zone": zone, "street": via_nome, "street_type": via_tipo, "distance_m": dist} if zone else None
