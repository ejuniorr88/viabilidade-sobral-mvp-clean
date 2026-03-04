import os
import json
import pathlib
from pathlib import Path
from typing import Any, Dict

import streamlit as st

# =============================
# Debug markers (garante que o deploy está lendo o app.py correto)
# =============================
st.write("APP VERSION MARKER: 2026-03-03-XYZ")
st.write("CWD:", os.getcwd())
st.write("FILES in data/:", [p.name for p in pathlib.Path("data").glob("*")])

# =============================
# Config
# =============================
st.set_page_config(layout="wide", page_title="Viabilidade")
st.title("Viabilidade")

DATA_DIR = Path("data")
ZONE_FILE = DATA_DIR / "zoneamento_light.json"

# =============================
# Imports do projeto (robustos)
# =============================
# Zonas (alguns branches renomearam o módulo)
try:
    from core.zones_map import load_zones
except Exception:
    from core.zones_mapa import load_zones  # type: ignore

# Streets (alguns projetos usam load_streets() sem args)
try:
    from core.streets import load_streets  # noqa
except Exception:
    load_streets = None  # type: ignore

# Supabase rules
try:
    from core.supabase_rules import fetch_rule, pick_rule  # type: ignore
except Exception:
    # fallback: caso o arquivo tenha outro nome
    from core.supabase_rule import fetch_rule, pick_rule  # type: ignore

# UI
from ui.mapa import render_mapa_section
from ui.lote import render_lote_section
from ui.localizacao import render_localizacao_section
from ui.indices import render_indices_section
from ui.analise import render_analise_section
from ui.relatorio import render_relatorio_section


# =============================
# Cache
# =============================
@st.cache_data(show_spinner=False)
def _zones_geojson() -> Dict[str, Any]:
    with open(ZONE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_resource(show_spinner=False)
def _zones_prepared():
    return load_zones(ZONE_FILE)

# =============================
# Estado inicial
# =============================
if "selected_lat" not in st.session_state:
    st.session_state.selected_lat = None
if "selected_lon" not in st.session_state:
    st.session_state.selected_lon = None

# A UI usa st.session_state.calc (dict) - contrato mínimo
if "calc" not in st.session_state or not isinstance(st.session_state.calc, dict):
    st.session_state.calc = {}

# contrato (não mudar chaves; outras seções dependem)
_calc_defaults = {
    "ok": False,
    "err": None,
    "zone": None,
    "zone_sigla": None,  # alias compat
    "use_type_code": "RES_UNI",
    "street_info": None,
    "street_name": None,
    "street_type": None,
    "street_dist": None,
    "via_nome": None,
    "via_tipo": None,
    "via_dist_m": None,
    "rule": None,
    "ia_utilizado": None,
    "to_utilizada_pct": None,
    "tp_prevista_pct": None,
    "basic": None,
}

for _k, _v in _calc_defaults.items():
    st.session_state.calc.setdefault(_k, _v)



# =============================
# Carregar bases
# =============================
zones_gj = _zones_geojson()
zones_prepared = _zones_prepared()

# =============================
# Pequena função de card (evita dependência externa)
# =============================
def _card(title: str, value: Any, suffix: str = "") -> None:
    v = "—" if value is None or value == "" else f"{value}{suffix}"
    st.markdown(
        f"""
        <div style="padding:12px;border:1px solid #e7e7e7;border-radius:12px;margin-bottom:10px;">
            <div style="font-size:12px;opacity:.75">{title}</div>
            <div style="font-size:20px;font-weight:700">{v}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================
# 1) Mapa (seleciona lat/lon e define raio)
# =============================
radius_m = render_mapa_section(zones_gj)

# Botão (mantém o fluxo)
calcular = st.button("🔎 Calcular viabilidade", key="btn_calc")

# =============================
# 2) Dados do lote (RETORNA 3 valores SEM erro)
# =============================
lot_area, built_ground, permeable_area = render_lote_section()

# =============================
# 3) Localização (zona + via)
# =============================
# Localização escreve em st.session_state.calc (zone, via, tipo_via, dist_m, ok, err)
_ = render_localizacao_section(calcular, zones_prepared, radius_m)

# =============================
# Opção B: garantir que a REGRA vem do Supabase assim que tiver zona
# =============================
calc = st.session_state.calc
if calcular and calc.get("ok") and calc.get("zone") and not calc.get("rule") and not calc.get("err"):
    try:
        rule = fetch_rule(calc["zone"], calc.get("use_type_code") or "RES_UNI")
        if rule:
            calc["rule"] = rule
        else:
            calc["err"] = f"Nenhuma regra no Supabase para zona={calc['zone']} e uso={calc.get('use_type_code')}"
    except Exception as e:
        calc["err"] = f"Erro ao consultar Supabase: {e}"

# =============================
# 4) Índices Urbanísticos (Supabase)
# =============================
render_indices_section(calc=calc, card_func=_card, pick_func=pick_rule, get_rule_func=fetch_rule)

# =============================
# 5) Análise Urbanística
# =============================
render_analise_section(
    calc,
    lot_area=lot_area,
    built_ground=built_ground,
    permeable_area=permeable_area,
    pick_func=pick_rule,
)

# =============================
# 6) Relatório Urbanístico
# =============================
render_relatorio_section(calc)


# =============================
# Diagnóstico técnico (opcional)
# =============================
with st.expander("🛠️ Diagnóstico técnico (para debug / deploy)"):
    st.write("Python:", os.sys.version)
    st.write("Supabase env vars presentes:",
             bool(os.getenv("SUPABASE_URL")),
             bool(os.getenv("SUPABASE_ANON_KEY")))
    st.write("Último clique no mapa (last_click):", st.session_state.get("last_click"))
    st.write("Raio atual (radius_m):", radius_m)
    st.write("Lote (inputs):", {"lot_area": lot_area, "built_ground": built_ground, "permeable_area": permeable_area})
    st.subheader("calc (estado completo)")
    st.json(st.session_state.calc)
