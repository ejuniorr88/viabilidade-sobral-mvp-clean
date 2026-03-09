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

# Supabase auth client
try:
    from core.supabase_client import get_supabase
except Exception:
    get_supabase = None  # type: ignore

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

# A UI usa st.session_state.calc (dict)
if "calc" not in st.session_state or not isinstance(st.session_state.calc, dict):
    st.session_state.calc = {}

# valor default do tipo de uso
st.session_state.calc.setdefault("use_type_code", "RES_UNI")


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


def _read_secret_or_env(key: str, default: str | None = None) -> str | None:
    val = os.getenv(key)
    if val:
        return val
    try:
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return default


def _clear_query_params() -> None:
    try:
        st.query_params.clear()
    except Exception:
        try:
            st.experimental_set_query_params()
        except Exception:
            pass


def _extract_response_attr(obj: Any, name: str):
    if obj is None:
        return None
    if hasattr(obj, name):
        return getattr(obj, name)
    if isinstance(obj, dict):
        return obj.get(name)
    return None


def _exchange_oauth_code_if_present() -> None:
    if get_supabase is None:
        return

    code = None
    try:
        code = st.query_params.get("code")
    except Exception:
        try:
            code = st.experimental_get_query_params().get("code", [None])[0]
        except Exception:
            code = None

    if not code or st.session_state.get("oauth_code_processed") == code:
        return

    try:
        supabase = get_supabase()
        supabase.auth.exchange_code_for_session({"auth_code": code})
        st.session_state["oauth_code_processed"] = code
        st.session_state.pop("google_auth_url", None)
        _clear_query_params()
        st.session_state["auth_feedback"] = "Login realizado com sucesso."
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao concluir login Google: {e}")


def _current_user_info() -> tuple[Any, Any]:
    if get_supabase is None:
        return None, None

    try:
        supabase = get_supabase()
        session_resp = supabase.auth.get_session()
        session = _extract_response_attr(session_resp, "session")
        if not session:
            return None, None

        user_resp = supabase.auth.get_user()
        user = _extract_response_attr(user_resp, "user")
        return session, user
    except Exception:
        return None, None


def _user_email(user: Any) -> str | None:
    if user is None:
        return None
    if hasattr(user, "email"):
        return getattr(user, "email")
    if isinstance(user, dict):
        return user.get("email")
    return None


def _user_name(user: Any) -> str | None:
    if user is None:
        return None
    for attr in ("name", "full_name"):
        if hasattr(user, attr):
            val = getattr(user, attr)
            if val:
                return val
    if hasattr(user, "user_metadata"):
        md = getattr(user, "user_metadata") or {}
        if isinstance(md, dict):
            return md.get("full_name") or md.get("name")
    if isinstance(user, dict):
        md = user.get("user_metadata") or {}
        if isinstance(md, dict):
            return md.get("full_name") or md.get("name")
        return user.get("full_name") or user.get("name")
    return None


def render_google_login_top() -> None:
    _exchange_oauth_code_if_present()

    st.markdown("### Conta")
    st.caption("Entre com Google para acessar créditos, pagamentos, histórico e carteira de créditos.")

    if get_supabase is None:
        st.warning("Cliente Supabase não disponível para iniciar o login Google.")
        st.divider()
        return

    feedback = st.session_state.pop("auth_feedback", None)
    if feedback:
        st.success(feedback)

    session, user = _current_user_info()
    user_email = _user_email(user)
    user_name = _user_name(user)

    if user:
        col1, col2, col3 = st.columns([2.2, 1.6, 1.0])
        with col1:
            st.success(f"Logado com Google: {user_name or user_email or 'usuário autenticado'}")
            if user_email:
                st.caption(user_email)
        with col2:
            st.caption("Sua sessão está ativa neste navegador.")
        with col3:
            if st.button("Sair", use_container_width=True, key="btn_google_logout"):
                try:
                    supabase = get_supabase()
                    supabase.auth.sign_out()
                except Exception as e:
                    st.error(f"Erro ao sair da conta: {e}")
                finally:
                    for k in ["google_auth_url", "oauth_code_processed", "auth_feedback"]:
                        st.session_state.pop(k, None)
                    _clear_query_params()
                    st.rerun()
        st.divider()
        return

    app_url = _read_secret_or_env("APP_URL", "http://localhost:8501")

    col1, col2 = st.columns([1.2, 2.8])
    with col1:
        if st.button("Entrar com Google", use_container_width=True, key="btn_google_login"):
            try:
                supabase = get_supabase()
                response = supabase.auth.sign_in_with_oauth(
                    {
                        "provider": "google",
                        "options": {"redirect_to": app_url},
                    }
                )

                auth_url = None
                if hasattr(response, "url"):
                    auth_url = response.url
                elif isinstance(response, dict):
                    auth_url = response.get("url")

                if auth_url:
                    st.session_state["google_auth_url"] = auth_url
                else:
                    st.error("Não foi possível gerar o link de login com Google.")
            except Exception as e:
                st.error(f"Erro ao iniciar login Google: {e}")

    with col2:
        auth_url = st.session_state.get("google_auth_url")
        if auth_url:
            st.link_button("Continuar login no Google", auth_url, use_container_width=False)
            st.info("Depois de concluir o login, você voltará para o app e o topo mostrará claramente que a conta está logada.")
        else:
            st.caption("Ao clicar, o sistema gera o link seguro de autenticação do Google via Supabase.")

    st.divider()

render_google_login_top()


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

# guarda info do lote para o relatório
st.session_state.calc["lot_area_m2"] = float(lot_area)
st.session_state.calc["lot_front_m"] = float(st.session_state.get("lot_front_m") or 0.0)
st.session_state.calc["lot_depth_m"] = float(st.session_state.get("lot_depth_m") or 0.0)
st.session_state.calc["lot_is_corner"] = bool(st.session_state.get("lot_is_corner", False))

# =============================
# 3) Localização (zona + via)
# =============================
# Localização escreve em st.session_state.calc (zone, via, tipo_via, dist_m, ok, err)
_ = render_localizacao_section(calcular, zones_prepared, radius_m)

# =============================
# Opção B: garantir que a REGRA vem do Supabase assim que tiver zona
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
