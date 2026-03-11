import os
import json
import pathlib
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st
import streamlit.components.v1 as components

st.write("APP VERSION MARKER: 2026-03-09-MP-PIX-TEST-V1")
st.write("CWD:", os.getcwd())
st.write("FILES in data/:", [p.name for p in pathlib.Path("data").glob("*")])

st.set_page_config(layout="wide", page_title="Viabilidade")

DATA_DIR = Path("data")
ZONE_FILE = DATA_DIR / "zoneamento_light.json"

try:
    from core.zones_map import load_zones
except Exception:
    from core.zones_mapa import load_zones  # type: ignore

try:
    from core.streets import load_streets  # noqa
except Exception:
    load_streets = None  # type: ignore

try:
    from core.supabase_rules import fetch_rule, pick_rule  # type: ignore
except Exception:
    from core.supabase_rule import fetch_rule, pick_rule  # type: ignore

from ui.mapa import render_mapa_section
from ui.lote import render_lote_section
from ui.localizacao import render_localizacao_section
from ui.indices import render_indices_section
from ui.analise import render_analise_section
from ui.relatorio import render_relatorio_section
from core.auth import handle_oauth_callback, start_google_login
from ui.auth_panel import render_google_login_top
from ui.credits_panel import render_credits_panel
from ui.payments_panel import render_payments_panel


@st.cache_data(show_spinner=False)
def _zones_geojson() -> Dict[str, Any]:
    with open(ZONE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_resource(show_spinner=False)
def _zones_prepared():
    return load_zones(ZONE_FILE)


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


def _render_login_gate_block() -> None:
    """
    Bloco inferior de login.
    Patch mínimo:
    - aparece só quando o usuário tenta calcular sem estar logado
    - não mexe no fluxo do topo
    """
    st.markdown("### Faça login para continuar")
    st.info("Para liberar a pesquisa de viabilidade, entre com sua conta Google.")

    auth_url = None
    try:
        auth_url = start_google_login()
    except Exception:
        auth_url = None

    if auth_url:
        st.link_button(
            "Entrar com Google",
            auth_url,
            use_container_width=True,
        )
        st.caption("O login será aberto em nova aba. Depois volte para esta aba.")
    else:
        st.error("Não foi possível gerar o link de login com Google.")


# =============================
# Estado base do app
# =============================
if "selected_lat" not in st.session_state:
    st.session_state.selected_lat = None
if "selected_lon" not in st.session_state:
    st.session_state.selected_lon = None
if "calc" not in st.session_state or not isinstance(st.session_state.calc, dict):
    st.session_state.calc = {}
st.session_state.calc.setdefault("use_type_code", "RES_UNI")

# =============================
# Flags do patch mínimo
# Separadas para não quebrar o que já existe
# =============================
if "show_login_gate" not in st.session_state:
    st.session_state.show_login_gate = False
if "scroll_to_login_gate" not in st.session_state:
    st.session_state.scroll_to_login_gate = False
if "scroll_to_item3" not in st.session_state:
    st.session_state.scroll_to_item3 = False
if "post_login_action" not in st.session_state:
    st.session_state.post_login_action = None

handle_oauth_callback()

zones_gj = _zones_geojson()
zones_prepared = _zones_prepared()

st.title("Viabilidade")
render_google_login_top()
render_credits_panel(_card)
render_payments_panel()
st.divider()

radius_m = render_mapa_section(zones_gj)
clicked_calcular = st.button("🔎 Calcular viabilidade", key="btn_calc")

lot_area, built_ground, permeable_area = render_lote_section()

st.session_state.calc["lot_area_m2"] = float(lot_area)
st.session_state.calc["lot_front_m"] = float(st.session_state.get("lot_front_m") or 0.0)
st.session_state.calc["lot_depth_m"] = float(st.session_state.get("lot_depth_m") or 0.0)
st.session_state.calc["lot_is_corner"] = bool(st.session_state.get("lot_is_corner", False))

auth_logged_in = bool(st.session_state.get("auth_logged_in"))

# ==========================================================
# Patch mínimo:
# controla só a liberação do cálculo, sem mexer no resto do app
# ==========================================================
calcular = False

if clicked_calcular:
    if not auth_logged_in:
        # Sem login: não libera a pesquisa.
        # Só mostra o bloco inferior e desce para ele.
        st.session_state.show_login_gate = True
        st.session_state.scroll_to_login_gate = True
        st.session_state.post_login_action = "calculate_viability"
    else:
        # Com login: segue o fluxo normal do app.
        st.session_state.show_login_gate = False
        calcular = True
        st.session_state.scroll_to_item3 = True

# ==========================================================
# Continuação automática após login
# Mantém a intenção do usuário sem reescrever o fluxo de cálculo
# ==========================================================
if auth_logged_in and st.session_state.get("post_login_action") == "calculate_viability":
    calcular = True
    st.session_state.post_login_action = None
    st.session_state.show_login_gate = False
    st.session_state.scroll_to_item3 = True

# ==========================================================
# Âncora + bloco inferior de login
# ==========================================================
st.markdown('<div id="login-gate-start"></div>', unsafe_allow_html=True)

if st.session_state.get("show_login_gate") and not auth_logged_in:
    _render_login_gate_block()
    st.divider()

# ==========================================================
# Âncora do começo do Item 3
# ==========================================================
st.markdown('<div id="item-3-start"></div>', unsafe_allow_html=True)

# Comentário importante:
# aqui preservamos a chamada original do sistema.
# A única diferença é que "calcular" agora só vira True quando o login permite.
_ = render_localizacao_section(calcular, zones_prepared, radius_m)

calc = st.session_state.calc

# Mantido igual à lógica original:
# só busca regra quando o cálculo realmente foi liberado
if calcular and calc.get("zone") and not calc.get("rule") and not calc.get("err"):
    try:
        rule = fetch_rule(calc["zone"], calc.get("use_type_code") or "RES_UNI")
        if rule:
            calc["rule"] = rule
        else:
            calc["err"] = f"Nenhuma regra no Supabase para zona={calc['zone']} e uso={calc.get('use_type_code')}"
    except Exception as e:
        calc["err"] = f"Erro ao consultar Supabase: {e}"

render_indices_section(calc=calc, card_func=_card, pick_func=pick_rule, get_rule_func=fetch_rule)
render_analise_section(
    calc,
    lot_area=lot_area,
    built_ground=built_ground,
    permeable_area=permeable_area,
    pick_func=pick_rule,
)
render_relatorio_section(calc)

# ==========================================================
# Scroll isolado para o login inferior
# ==========================================================
if st.session_state.get("scroll_to_login_gate"):
    components.html(
        """
        <script>
            const rootDoc = window.parent.document;
            const el = rootDoc.getElementById("login-gate-start");
            if (el) {
                el.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        </script>
        """,
        height=0,
    )
    st.session_state.scroll_to_login_gate = False

# ==========================================================
# Scroll isolado para o começo do item 3
# ==========================================================
if st.session_state.get("scroll_to_item3"):
    components.html(
        """
        <script>
            const rootDoc = window.parent.document;
            const el = rootDoc.getElementById("item-3-start");
            if (el) {
                el.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        </script>
        """,
        height=0,
    )
    st.session_state.scroll_to_item3 = False
