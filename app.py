# app.py
# Viabilidade MVP (Streamlit)
# - Mantém: mapa, Supabase, vagas v2, sanitários, debug
# - Entrega: seção "Viabilidade (para leigo)" funcionando para Residencial Unifamiliar e Multifamiliar

from __future__ import annotations

import os
import math
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

# ---------------------------
# Optional dependencies
# ---------------------------
SUPABASE_AVAILABLE = True
try:
    from supabase import create_client, Client  # type: ignore
except Exception:
    SUPABASE_AVAILABLE = False
    Client = Any  # type: ignore

MAP_AVAILABLE = True
try:
    import pydeck as pdk  # type: ignore
except Exception:
    MAP_AVAILABLE = False
    pdk = None  # type: ignore


# ===========================
# Config / Constants
# ===========================
APP_TITLE = "Viabilidade Urbana – MVP"
DEFAULT_CENTER = (-3.689, -40.349)  # Sobral-CE (aprox.)
USE_CODES = {
    "Residencial Unifamiliar": "RES_UNI",
    "Residencial Multifamiliar": "RES_MULTI",
}

# Fallback (quando Supabase não está configurado ou as tabelas não existem)
FALLBACK_RULES = {
    # Estes números são apenas para o app não quebrar.
    # O correto é vir do Supabase (suas tabelas consolidadas).
    ("ZAP", "RES_UNI"): {
        "zone_sigla": "ZAP",
        "use_type_code": "RES_UNI",
        "tp_min": 0.10,
        "to_max": 0.60,
        "ia_max": 1.50,
        "max_height_m": 9.0,
        "setback_front_m": 3.0,
        "setback_side_m": 1.5,
        "setback_back_m": 2.0,
        "allow_attach_one_side": True,
        "notes": "Fallback: revise no Supabase.",
    },
    ("ZAP", "RES_MULTI"): {
        "zone_sigla": "ZAP",
        "use_type_code": "RES_MULTI",
        "tp_min": 0.10,
        "to_max": 0.50,
        "ia_max": 2.00,
        "max_height_m": 18.0,
        "setback_front_m": 5.0,
        "setback_side_m": 2.0,
        "setback_back_m": 3.0,
        "allow_attach_one_side": False,
        "notes": "Fallback: revise no Supabase.",
    },
}

# ===========================
# Helpers
# ===========================
def _coalesce(d: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Try multiple keys (aliases) and return the first non-null/exists value."""
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default

def _fmt_pct(x: Optional[float]) -> str:
    if x is None:
        return "—"
    return f"{x*100:.0f}%"

def _fmt_m(x: Optional[float]) -> str:
    if x is None:
        return "—"
    if isinstance(x, (int, float)):
        return f"{x:.2f} m".replace(".00", "")
    return str(x)

def _fmt_num(x: Optional[float]) -> str:
    if x is None:
        return "—"
    if isinstance(x, (int, float)):
        if abs(x - round(x)) < 1e-9:
            return f"{int(round(x))}"
        return f"{x:.2f}".rstrip("0").rstrip(".")
    return str(x)

def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None or x == "":
            return None
        return float(x)
    except Exception:
        return None

def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

def _area_buildable_estimate(
    lot_area: float,
    to_max: Optional[float],
    ia_max: Optional[float],
    floors: int,
) -> Tuple[Optional[float], Optional[float]]:
    """
    Estimate:
    - max_footprint = lot_area * TO
    - max_total_built = lot_area * IA
    If both exist, compute implied footprint by IA/floors.
    """
    max_footprint = (lot_area * to_max) if to_max is not None else None
    max_total_built = (lot_area * ia_max) if ia_max is not None else None
    return max_footprint, max_total_built

@dataclass
class ViabilityInputs:
    zone_sigla: str
    via_class: str
    use_label: str
    use_code: str
    lot_area_m2: float
    lot_front_m: Optional[float]
    floors: int
    built_area_target_m2: Optional[float]  # what user wants

@dataclass
class ZoneRule:
    raw: Dict[str, Any]

    # behave like a dict (helps st.json, calculations, etc.)
    def get(self, key: str, default: Any = None) -> Any:
        return self.raw.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.raw)

    @property
    def tp_min(self) -> Optional[float]:
        return _safe_float(_coalesce(self.raw, "tp_min", "taxa_permeabilidade_min", "tp"))

    @property
    def to_max(self) -> Optional[float]:
        return _safe_float(_coalesce(self.raw, "to_max", "taxa_ocupacao_max", "to", "to_solo_max"))

    @property
    def ia_max(self) -> Optional[float]:
        return _safe_float(_coalesce(self.raw, "ia_max", "indice_aproveitamento_max", "ia"))

    @property
    def max_height_m(self) -> Optional[float]:
        return _safe_float(_coalesce(self.raw, "max_height_m", "altura_max_m", "altura_maxima_m", "gabarito_m"))

    @property
    def setback_front_m(self) -> Optional[float]:
        return _safe_float(_coalesce(self.raw, "setback_front_m", "recuo_frontal_m", "front_setback_m", "recuo_frente_m"))

    @property
    def setback_side_m(self) -> Optional[float]:
        return _safe_float(_coalesce(self.raw, "setback_side_m", "recuo_lateral_m", "side_setback_m", "recuo_lados_m"))

    @property
    def setback_back_m(self) -> Optional[float]:
        return _safe_float(_coalesce(self.raw, "setback_back_m", "recuo_fundos_m", "back_setback_m", "recuo_fundo_m"))

    @property
    def allow_attach_one_side(self) -> bool:
        v = _coalesce(self.raw, "allow_attach_one_side", "permite_encostar_uma_lateral", default=False)
        return bool(v)

    @property
    def notes(self) -> str:
        return str(_coalesce(self.raw, "notes", "observacoes", default="")).strip()

# ===========================
# Supabase
# ===========================
@st.cache_resource(show_spinner=False)
def get_supabase() -> Optional["Client"]:
    if not SUPABASE_AVAILABLE:
        return None

    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_ANON_KEY", "").strip()
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None

def sb_select_one(sb: "Client", table: str, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    q = sb.table(table).select("*")
    for k, v in filters.items():
        q = q.eq(k, v)
    res = q.limit(1).execute()
    data = getattr(res, "data", None)
    if not data:
        return None
    return data[0]

def sb_select_many(sb: "Client", table: str, filters: Dict[str, Any], limit: int = 200) -> List[Dict[str, Any]]:
    q = sb.table(table).select("*")
    for k, v in filters.items():
        q = q.eq(k, v)
    res = q.limit(limit).execute()
    data = getattr(res, "data", None)
    return data or []

def fetch_zone_rule(sb: Optional["Client"], zone_sigla: str, use_code: str) -> ZoneRule:
    # Try Supabase first
    if sb is not None:
        # common table name: zone_rules
        try:
            row = sb_select_one(sb, "zone_rules", {"zone_sigla": zone_sigla, "use_type_code": use_code})
            if row:
                return ZoneRule(row)
        except Exception:
            pass

        # alternative possibilities
        for alt_table in ("zone_rule", "zone_params", "zone_parameters"):
            try:
                row = sb_select_one(sb, alt_table, {"zone_sigla": zone_sigla, "use_type_code": use_code})
                if row:
                    return ZoneRule(row)
            except Exception:
                continue

    # Fallback
    row = FALLBACK_RULES.get((zone_sigla, use_code), {
        "zone_sigla": zone_sigla,
        "use_type_code": use_code,
        "notes": "Nenhuma regra encontrada no Supabase. Configure as tabelas e/ou revise a sigla da zona.",
    })
    return ZoneRule(row)

# ===========================
# Vagas v2 (Estacionamento)
# ===========================
def calc_parking_v2(sb: Optional["Client"], use_code: str, built_area_m2: float, units: Optional[int]) -> Dict[str, Any]:
    """
    Attempts to calculate parking using a 'parking_rules_v2' table.
    Expected patterns (flexible):
      - key by use_type_code
      - rule types:
          * per_m2: 1 vaga a cada X m²
          * per_unit: 1 vaga por unidade
          * fixed: mínimo fixo
    The function returns a dict with the computed result and debugging fields.
    """
    out: Dict[str, Any] = {"source": "fallback", "vagas": None, "details": ""}

    if sb is not None:
        for table in ("parking_rules_v2", "parking_rules", "vagas_regras_v2"):
            try:
                rule = sb_select_one(sb, table, {"use_type_code": use_code})
                if rule:
                    out["source"] = table
                    rule_type = str(_coalesce(rule, "rule_type", "tipo_regra", default="")).lower()
                    ratio_m2 = _safe_float(_coalesce(rule, "ratio_m2", "m2_por_vaga", "area_por_vaga"))
                    per_unit = _safe_float(_coalesce(rule, "vagas_por_unidade", "ratio_unit"))
                    minimum = _safe_float(_coalesce(rule, "min_vagas", "minimo", default=0))
                    rounding = str(_coalesce(rule, "rounding", "arredondamento", default="ceil")).lower()

                    vagas = 0.0
                    if rule_type in ("per_m2", "m2", "area"):
                        if ratio_m2 and ratio_m2 > 0:
                            vagas = built_area_m2 / ratio_m2
                        else:
                            vagas = 0
                    elif rule_type in ("per_unit", "unit", "unidade"):
                        if units is None:
                            # estimate units for multifamiliar: assume 1 unit per 60 m2 if unknown
                            est_units = max(1, int(math.ceil(built_area_m2 / 60.0)))
                            units = est_units
                        vagas = (per_unit or 1.0) * float(units)
                    elif rule_type in ("fixed", "fixo"):
                        vagas = _safe_float(_coalesce(rule, "fixed_vagas", "vagas_fixas", default=0)) or 0
                    else:
                        # try ratio_m2 if present
                        if ratio_m2 and ratio_m2 > 0:
                            vagas = built_area_m2 / ratio_m2

                    # rounding
                    if rounding == "floor":
                        vagas = math.floor(vagas)
                    elif rounding == "round":
                        vagas = round(vagas)
                    else:
                        vagas = math.ceil(vagas)

                    if minimum is not None:
                        vagas = max(vagas, float(minimum))

                    out["vagas"] = int(vagas)
                    out["details"] = f"rule_type={rule_type or 'auto'}, built_area={built_area_m2:.1f}m², units={units}, minimum={minimum}"
                    return out
            except Exception:
                continue

    # fallback heuristic:
    if use_code == "RES_UNI":
        out["vagas"] = 1 if built_area_m2 <= 200 else 2
        out["details"] = "Heurística: unifamiliar 1 vaga até 200m²; acima 2."
    elif use_code == "RES_MULTI":
        # assume 1 vaga por unidade; estimate units
        est_units = max(1, int(math.ceil(built_area_m2 / 60.0)))
        out["vagas"] = est_units
        out["details"] = f"Heurística: 1 vaga/unidade. Unidades estimadas={est_units} (60m²/unid)."
    else:
        out["vagas"] = None
        out["details"] = "Sem regra."
    return out

# ===========================
# Sanitários (Anexo III)
# ===========================
def calc_sanitary(sb: Optional["Client"], use_code: str, built_area_m2: float, people: Optional[int]) -> Dict[str, Any]:
    """
    Attempts to calculate sanitary fixtures based on a 'sanitary_rules' table.
    For Residential uses: typically not required like commerce; we'll return 'não aplicável'
    unless your DB has explicit rules.
    """
    out: Dict[str, Any] = {"source": "fallback", "items": {}, "details": ""}

    if sb is not None:
        for table in ("sanitary_rules", "sanitary_requirements", "instalacoes_sanitarias"):
            try:
                rule = sb_select_one(sb, table, {"use_type_code": use_code})
                if rule:
                    out["source"] = table
                    # Flexible: store rule as JSON and let UI display it
                    out["items"] = rule
                    out["details"] = "Regra encontrada no Supabase (exibida em debug)."
                    return out
            except Exception:
                continue

    # fallback
    if use_code in ("RES_UNI", "RES_MULTI"):
        out["items"] = {"status": "Não aplicável (residencial)", "observacao": "Regras de sanitários do Anexo III normalmente se aplicam a usos como comércio/serviços. Se você modelou regras residenciais, elas virão do Supabase."}
        out["details"] = "Fallback."
    else:
        out["items"] = {"status": "Sem regra"}
        out["details"] = "Fallback."
    return out

# ===========================
# Viabilidade (para leigo)
# ===========================
def build_leigo_report(inputs: ViabilityInputs, rule: ZoneRule) -> Dict[str, Any]:
    """
    Return structured, layperson-friendly results for RES_UNI and RES_MULTI.
    """
    lot_area = inputs.lot_area_m2
    floors = max(1, int(inputs.floors))
    to_max = rule.to_max
    tp_min = rule.tp_min
    ia_max = rule.ia_max

    max_footprint, max_total_built = _area_buildable_estimate(lot_area, to_max, ia_max, floors)

    # If user has a target, assess plausibility
    target = inputs.built_area_target_m2
    ok_by_ia = None
    if target is not None and max_total_built is not None:
        ok_by_ia = target <= max_total_built + 1e-9

    # rough permeable area minimum:
    min_permeable = (lot_area * tp_min) if tp_min is not None else None

    # setbacks message:
    can_attach = rule.allow_attach_one_side
    if inputs.use_code == "RES_UNI":
        attach_msg = "Pode encostar em 1 lateral" if can_attach else "Em regra, não encosta (precisa manter recuo lateral)"
    else:
        attach_msg = "Só pode encostar se houver regra específica liberando" if can_attach else "Normalmente precisa manter recuos laterais"

    return {
        "zone": inputs.zone_sigla,
        "via": inputs.via_class,
        "use_code": inputs.use_code,
        "use_label": inputs.use_label,
        "setbacks": {
            "front": rule.setback_front_m,
            "side": rule.setback_side_m,
            "back": rule.setback_back_m,
            "attach_one_side": can_attach,
            "attach_msg": attach_msg,
        },
        "indices": {
            "tp_min": tp_min,
            "to_max": to_max,
            "ia_max": ia_max,
            "max_height_m": rule.max_height_m,
        },
        "areas": {
            "lot_area_m2": lot_area,
            "min_permeable_m2": min_permeable,
            "max_footprint_m2": max_footprint,
            "max_total_built_m2": max_total_built,
            "floors_assumed": floors,
            "target_built_m2": target,
            "target_ok_by_ia": ok_by_ia,
        },
        "notes": rule.notes,
    }

def render_leigo(report: Dict[str, Any]) -> None:
    use_label = report["use_label"]
    st.subheader("Viabilidade (para leigo)")

    st.markdown(
        f"""
**O que você está tentando fazer:** {use_label}  
**Onde:** Zona **{report['zone']}** · Via **{report['via']}**
"""
    )

    # 1) Recuos / encostar
    s = report["setbacks"]
    st.markdown("### 1) Recuos (espaços mínimos até a divisa)")
    cols = st.columns(3)
    cols[0].metric("Recuo frontal", _fmt_m(s["front"]))
    cols[1].metric("Recuo lateral (cada lado)", _fmt_m(s["side"]))
    cols[2].metric("Recuo fundos", _fmt_m(s["back"]))
    st.info(s["attach_msg"])

    # 2) Índices
    ind = report["indices"]
    st.markdown("### 2) Limites do terreno (índices)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Permeabilidade mínima (TP)", _fmt_pct(ind["tp_min"]))
    c2.metric("Ocupação máxima (TO)", _fmt_pct(ind["to_max"]))
    c3.metric("Aproveitamento máximo (IA)", _fmt_num(ind["ia_max"]))
    c4.metric("Altura máx. (gabarito)", _fmt_m(ind["max_height_m"]))

    # 3) Quanto cabe (estimativa)
    st.markdown("### 3) Quanto dá para construir (estimativa rápida)")
    a = report["areas"]
    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("Área do lote", f"{a['lot_area_m2']:.1f} m²")
    cc2.metric("Área permeável mínima", "—" if a["min_permeable_m2"] is None else f"{a['min_permeable_m2']:.1f} m²")
    cc3.metric("Pavimentos considerados", str(a["floors_assumed"]))

    ccc1, ccc2 = st.columns(2)
    ccc1.metric("Máx. área ocupada no térreo (TO)", "—" if a["max_footprint_m2"] is None else f"{a['max_footprint_m2']:.1f} m²")
    ccc2.metric("Máx. área total construída (IA)", "—" if a["max_total_built_m2"] is None else f"{a['max_total_built_m2']:.1f} m²")

    if a["target_built_m2"] is not None:
        if a["target_ok_by_ia"] is None:
            st.warning("Você informou uma área alvo, mas não encontrei o IA no Supabase (ou não está preenchido).")
        elif a["target_ok_by_ia"]:
            st.success("Pela conta do IA, sua área alvo parece **dentro do limite**.")
        else:
            st.error("Pela conta do IA, sua área alvo parece **acima do limite** (precisa reduzir ou revisar parâmetros).")

    if report.get("notes"):
        st.caption(f"Observações: {report['notes']}")


# ===========================
# UI Sections
# ===========================
def render_map(lat: float, lon: float) -> None:
    st.subheader("Mapa")
    if MAP_AVAILABLE:
        df = [{"lat": lat, "lon": lon}]
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position="[lon, lat]",
            get_radius=20,
            pickable=False,
        )
        view_state = pdk.ViewState(latitude=lat, longitude=lon, zoom=15)
        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))
    else:
        st.map([{"lat": lat, "lon": lon}])

def render_debug(debug: Dict[str, Any]) -> None:
    st.subheader("Debug")
    st.json(debug)

def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)

    sb = get_supabase()

    with st.sidebar:
        st.header("Entrada")
        use_label = st.selectbox("Tipo de uso (MVP)", list(USE_CODES.keys()), index=0)
        use_code = USE_CODES[use_label]

        zone_sigla = st.text_input("Sigla da zona (ex.: ZAP, ZCR...)", value="ZAP").strip().upper()
        via_class = st.text_input("Classificação da via (ex.: Arterial, Coletora, Local...)", value="Local").strip()

        st.markdown("---")
        lot_area_m2 = st.number_input("Área do lote (m²)", min_value=1.0, value=200.0, step=10.0)
        lot_front_m = st.number_input("Testada (m) (opcional)", min_value=0.0, value=10.0, step=0.5)
        lot_front_m = None if lot_front_m == 0 else float(lot_front_m)

        floors = st.number_input("Nº de pavimentos (para estimativa)", min_value=1, max_value=50, value=2, step=1)
        built_area_target = st.number_input("Área construída que você quer (m²) (opcional)", min_value=0.0, value=0.0, step=10.0)
        built_area_target = None if built_area_target == 0 else float(built_area_target)

        st.markdown("---")
        lat = st.number_input("Latitude", value=float(DEFAULT_CENTER[0]), format="%.6f")
        lon = st.number_input("Longitude", value=float(DEFAULT_CENTER[1]), format="%.6f")

        st.markdown("---")
        show_debug = st.toggle("Mostrar debug", value=True)

        st.caption(
            "Supabase: configure variáveis de ambiente SUPABASE_URL e SUPABASE_ANON_KEY.\n"
            "Sem Supabase, o app roda com regras de fallback apenas para não quebrar."
        )

    # Map + quick summary row
    colA, colB = st.columns([1.2, 1])
    with colA:
        render_map(lat, lon)

    # Fetch rules
    rule = fetch_zone_rule(sb, zone_sigla, use_code)

    # Prepare inputs struct
    inputs = ViabilityInputs(
        zone_sigla=zone_sigla,
        via_class=via_class,
        use_label=use_label,
        use_code=use_code,
        lot_area_m2=float(lot_area_m2),
        lot_front_m=lot_front_m,
        floors=int(floors),
        built_area_target_m2=built_area_target,
    )

    report = build_leigo_report(inputs, rule)

    # Choose built area for parking calc: prefer target; else max_total_built/floors as proxy; else lot_area
    built_area_for_calc = built_area_target
    if built_area_for_calc is None:
        # if max_total_built exists, use 70% of it as a conservative "typical"; else lot_area
        max_total = report["areas"]["max_total_built_m2"]
        if max_total is not None:
            built_area_for_calc = float(max_total) * 0.7
        else:
            built_area_for_calc = float(lot_area_m2)

    # Vagas v2 & Sanitários
    # units optional: ask only if multifamiliar to improve calc
    units = None
    with colB:
        st.subheader("Resumo técnico (rápido)")
        st.write("Regra encontrada em:", "Supabase" if sb is not None else "Fallback/local")
        st.metric("TO máx.", _fmt_pct(rule.to_max))
        st.metric("IA máx.", _fmt_num(rule.ia_max))
        st.metric("TP mín.", _fmt_pct(rule.tp_min))
        st.metric("Altura máx.", _fmt_m(rule.max_height_m))

        if use_code == "RES_MULTI":
            units = st.number_input("Nº de unidades (para vagas v2)", min_value=0, value=0, step=1)
            units = None if units == 0 else int(units)

        parking = calc_parking_v2(sb, use_code, float(built_area_for_calc), units)
        st.markdown("---")
        st.subheader("Vagas (v2)")
        if parking.get("vagas") is None:
            st.warning("Não foi possível calcular vagas para este uso (sem regra).")
        else:
            st.metric("Vagas estimadas", str(parking["vagas"]))
            st.caption(parking.get("details", ""))

        sanitary = calc_sanitary(sb, use_code, float(built_area_for_calc), None)
        st.markdown("---")
        st.subheader("Sanitários")
        st.write(sanitary.get("items", {}))

    st.markdown("---")
    # Leigo section (requested)
    render_leigo(report)

    # Debug section (requested to keep)
    if show_debug:
        debug_payload = {
            "inputs": inputs.__dict__,
            "rule_raw": rule.raw,
            "report": report,
            "parking": parking,
            "sanitary": sanitary,
            "supabase_available": SUPABASE_AVAILABLE,
            "supabase_connected": sb is not None,
            "map_available": MAP_AVAILABLE,
        }
        render_debug(debug_payload)

if __name__ == "__main__":
    main()
