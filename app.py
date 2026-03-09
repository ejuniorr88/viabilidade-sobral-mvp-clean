import os
import json
import pathlib
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st
from supabase import create_client

# =============================
# Debug markers (garante que o deploy está lendo o app.py correto)
# =============================
st.write("APP VERSION MARKER: 2026-03-09-GOOGLE-AUTH-GATE-V1")
st.write("CWD:", os.getcwd())
st.write("FILES in data/:", [p.name for p in pathlib.Path("data").glob("*")])

# =============================
# Config
# =============================
st.set_page_config(layout="wide", page_title="Viabilidade")

DATA_DIR = Path("data")
ZONE_FILE = DATA_DIR / "zoneamento_light.json"

# =============================
# Imports do projeto (robustos)
# =============================
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


@st.cache_resource(show_spinner=False)
def get_supabase_auth_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)


# =============================
# Auth helpers
# =============================
def _get_app_url() -> str:
    return st.secrets.get("APP_URL", "http://localhost:8501")


def _safe_get_query_param(name: str) -> Optional[str]:
    try:
        value = st.query_params.get(name)
        if isinstance(value, list):
            return value[0] if value else None
        return value
    except Exception:
        params = st.experimental_get_query_params()
        values = params.get(name)
        if not values:
            return None
        return values[0]


def _clear_auth_query_params() -> None:
    try:
        st.query_params.clear()
    except Exception:
        try:
            st.experimental_set_query_params()
        except Exception:
            pass


def _extract_user_fields(user_obj: Any) -> Dict[str, Optional[str]]:
    email = None
    name = None
    uid = None

    if user_obj is None:
        return {"email": None, "name": None, "id": None}

    if isinstance(user_obj, dict):
        email = user_obj.get("email")
        uid = user_obj.get("id")
        meta = user_obj.get("user_metadata") or {}
        name = meta.get("full_name") or meta.get("name")
        return {"email": email, "name": name, "id": uid}

    email = getattr(user_obj, "email", None)
    uid = getattr(user_obj, "id", None)
    meta = getattr(user_obj, "user_metadata", None) or {}
    if isinstance(meta, dict):
        name = meta.get("full_name") or meta.get("name")
    else:
        name = getattr(meta, "full_name", None) or getattr(meta, "name", None)

    return {"email": email, "name": name, "id": uid}


def _store_user_in_state(user_obj: Any) -> None:
    info = _extract_user_fields(user_obj)
    st.session_state["auth_logged_in"] = bool(info.get("id") or info.get("email"))
    st.session_state["auth_user_email"] = info.get("email")
    st.session_state["auth_user_name"] = info.get("name")
    st.session_state["auth_user_id"] = info.get("id")


def _sync_user_from_current_session() -> None:
    supabase = get_supabase_auth_client()

    try:
        user_response = supabase.auth.get_user()
        user_obj = getattr(user_response, "user", None)
        if user_obj is None and isinstance(user_response, dict):
            user_obj = user_response.get("user")
        if user_obj is not None:
            _store_user_in_state(user_obj)
            return
    except Exception:
        pass

    if "auth_logged_in" not in st.session_state:
        st.session_state["auth_logged_in"] = False
        st.session_state["auth_user_email"] = None
        st.session_state["auth_user_name"] = None
        st.session_state["auth_user_id"] = None


def _handle_oauth_callback() -> None:
    code = _safe_get_query_param("code")
    if not code:
        return

    if st.session_state.get("last_oauth_code") == code:
        return

    supabase = get_supabase_auth_client()

    try:
        response = supabase.auth.exchange_code_for_session({"auth_code": code})
        user_obj = getattr(response, "user", None)
        session_obj = getattr(response, "session", None)

        if user_obj is None and isinstance(response, dict):
            user_obj = response.get("user")
            session_obj = response.get("session")

        if user_obj is None and session_obj is not None:
            user_obj = getattr(session_obj, "user", None)
            if user_obj is None and isinstance(session_obj, dict):
                user_obj = session_obj.get("user")

        if user_obj is not None:
            _store_user_in_state(user_obj)
            st.session_state["auth_message"] = "Login efetuado com sucesso."
            st.session_state["last_oauth_code"] = code
            _clear_auth_query_params()
            st.rerun()
        else:
            st.session_state["auth_logged_in"] = False
            st.session_state["auth_message"] = "O Google retornou ao app, mas não foi possível identificar o usuário logado."
    except Exception as e:
        st.session_state["auth_logged_in"] = False
        st.session_state["auth_message"] = f"Erro ao concluir o login Google: {e}"


def render_auth_gate_page() -> None:
    supabase = get_supabase_auth_client()
    _sync_user_from_current_session()

    st.markdown("""
        <style>
        .auth-wrap {
            max-width: 760px;
            margin: 3rem auto 0 auto;
            padding: 2rem 2rem 1.5rem 2rem;
            border: 1px solid #e9e9e9;
            border-radius: 20px;
            background: #ffffff;
        }
        .auth-title {
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: .5rem;
        }
        .auth-subtitle {
            color: #666;
            margin-bottom: 1.25rem;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="auth-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">Acesse a plataforma</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="auth-subtitle">Faça login com Google para entrar no sistema e acessar os recursos da plataforma.</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.get("auth_message"):
        msg = st.session_state.get("auth_message")
        if st.session_state.get("auth_logged_in"):
            st.success(msg)
        else:
            st.warning(msg)

    if st.session_state.get("auth_logged_in"):
        name = st.session_state.get("auth_user_name")
        email = st.session_state.get("auth_user_email")
        if name and email:
            st.success(f"Login concluído: {name} ({email})")
        elif email:
            st.success(f"Login concluído: {email}")
        else:
            st.success("Login concluído com sucesso.")

        col_a, col_b = st.columns([1, 1])
        with col_a:
            if st.button("Entrar na plataforma", use_container_width=True, key="btn_enter_platform"):
                st.session_state["auth_gate_open"] = True
                st.rerun()
        with col_b:
            if st.button("Sair", use_container_width=True, key="btn_logout_on_gate"):
                try:
                    supabase.auth.sign_out()
                except Exception:
                    pass
                for key in [
                    "auth_logged_in",
                    "auth_user_email",
                    "auth_user_name",
                    "auth_user_id",
                    "auth_message",
                    "last_oauth_code",
                    "auth_gate_open",
                ]:
                    st.session_state.pop(key, None)
                _clear_auth_query_params()
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
        return

    if st.button("Entrar com Google", use_container_width=True, key="btn_google_login_gate"):
        response = supabase.auth.sign_in_with_oauth(
            {
                "provider": "google",
                "options": {
                    "redirect_to": _get_app_url(),
                },
            }
        )

        auth_url = None
        if hasattr(response, "url"):
            auth_url = response.url
        elif isinstance(response, dict):
            auth_url = response.get("url")

        if auth_url:
            st.link_button("Continuar login no Google", auth_url, use_container_width=True)
            st.info("Clique no botão acima para abrir a autenticação do Google.")
        else:
            st.error("Não foi possível gerar o link de login com Google.")

    st.caption("O acesso à página principal só é liberado após o login.")
    st.markdown('</div>', unsafe_allow_html=True)


def render_google_login_top() -> None:
    supabase = get_supabase_auth_client()
    _sync_user_from_current_session()

    st.subheader("Conta")

    if st.session_state.get("auth_message"):
        msg = st.session_state.get("auth_message")
        if st.session_state.get("auth_logged_in"):
            st.success(msg)
        else:
            st.warning(msg)

    if st.session_state.get("auth_logged_in"):
        name = st.session_state.get("auth_user_name")
        email = st.session_state.get("auth_user_email")

        if name and email:
            st.success(f"Logado com Google: {name} ({email})")
        elif email:
            st.success(f"Logado com Google: {email}")
        else:
            st.success("Login Google ativo.")

        col_a, col_b = st.columns([1, 3])
        with col_a:
            if st.button("Sair", use_container_width=True, key="btn_google_logout"):
                try:
                    supabase.auth.sign_out()
                except Exception:
                    pass

                for key in [
                    "auth_logged_in",
                    "auth_user_email",
                    "auth_user_name",
                    "auth_user_id",
                    "auth_message",
                    "last_oauth_code",
                ]:
                    st.session_state.pop(key, None)

                _clear_auth_query_params()
                st.rerun()

        with col_b:
            st.caption("Sua sessão Google está ativa neste navegador.")
        return

    st.caption("Entre com Google para acessar créditos, pagamentos, histórico e carteira de créditos.")
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("Entrar com Google", use_container_width=True, key="btn_google_login"):
            response = supabase.auth.sign_in_with_oauth(
                {
                    "provider": "google",
                    "options": {
                        "redirect_to": _get_app_url(),
                    },
                }
            )

            auth_url = None
            if hasattr(response, "url"):
                auth_url = response.url
            elif isinstance(response, dict):
                auth_url = response.get("url")

            if auth_url:
                st.link_button("Continuar login no Google", auth_url, use_container_width=True)
                st.info("Clique no botão acima para abrir o login do Google.")
            else:
                st.error("Não foi possível gerar o link de login com Google.")

    with col2:
        st.caption("Ao clicar, o sistema gera o link seguro de autenticação do Google via Supabase.")


# =============================
# Estado inicial
# =============================
if "selected_lat" not in st.session_state:
    st.session_state.selected_lat = None
if "selected_lon" not in st.session_state:
    st.session_state.selected_lon = None
if "calc" not in st.session_state or not isinstance(st.session_state.calc, dict):
    st.session_state.calc = {}
st.session_state.calc.setdefault("use_type_code", "RES_UNI")
if "auth_gate_open" not in st.session_state:
    st.session_state.auth_gate_open = False

# Auth callback precisa rodar cedo, antes de renderizar a UI principal
_handle_oauth_callback()
_sync_user_from_current_session()

if st.session_state.get("auth_logged_in"):
    st.session_state.auth_gate_open = True

# =============================
# Tela de autenticação antes da página principal
# =============================
if not st.session_state.get("auth_gate_open"):
    st.title("Viabilidade")
    render_auth_gate_page()
    st.stop()

# =============================
# Carregar bases
# =============================
zones_gj = _zones_geojson()
zones_prepared = _zones_prepared()

# =============================
# UI topo
# =============================
st.title("Viabilidade")
render_google_login_top()
st.divider()


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

st.session_state.calc["lot_area_m2"] = float(lot_area)
st.session_state.calc["lot_front_m"] = float(st.session_state.get("lot_front_m") or 0.0)
st.session_state.calc["lot_depth_m"] = float(st.session_state.get("lot_depth_m") or 0.0)
st.session_state.calc["lot_is_corner"] = bool(st.session_state.get("lot_is_corner", False))

# =============================
# 3) Localização (zona + via)
# =============================
_ = render_localizacao_section(calcular, zones_prepared, radius_m)

# =============================
# Garantir que a REGRA vem do Supabase assim que tiver zona
# =============================
calc = st.session_state.calc
if calcular and calc.get("zone") and not calc.get("rule") and not calc.get("err"):
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
