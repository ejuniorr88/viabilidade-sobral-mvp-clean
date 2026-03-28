import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Viabilidade Fácil")

DATA_DIR = Path("data")
ZONE_FILE = DATA_DIR / "zoneamento_light.json"

try:
    from core.zones_map import load_zones
except Exception:
    from core.zones_mapa import load_zones  # type: ignore

try:
    from core.supabase_rules import fetch_rule, pick_rule  # type: ignore
except Exception:
    from core.supabase_rule import fetch_rule, pick_rule  # type: ignore

from ui.mapa import render_mapa_section
from ui.lote import render_lote_section
from ui.localizacao import render_localizacao_section
from ui.indices import render_indices_section
from ui.analise import render_analise_section
from ui.relatorio import (
    render_relatorio_section,
    render_zone_description_section,
    render_unifamiliar_inadequado_preview,
    should_block_unifamiliar_preview,
)
from core.auth import handle_oauth_callback, get_app_url, safe_get_query_param
from ui.auth_panel import render_google_login_top, render_google_login_box
from ui.payments_panel import render_payments_panel
from ui.relatorio_blocks.multifamiliar_guia import (
    render_multifamiliar_inadequado_preview,
    should_block_multifamiliar_preview,
)
from ui.client_area import render_client_area_page
from core.credits import consume_viability_credit, get_credit_balance, reconcile_wallet_to_current_user
from core.report_pdf import generate_report_pdf_bytes
from core.client_reports import save_client_report, build_report_signature


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
        <div style="padding:12px;border:1px solid #e7e7e7;border-radius:12px;margin-bottom:10px;background:#fff;">
            <div style="font-size:12px;opacity:.75">{title}</div>
            <div style="font-size:20px;font-weight:700">{v}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def _inject_global_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 0.4rem !important;
            padding-bottom: 2rem !important;
            max-width: 100% !important;
        }

        html, body, [data-testid="stAppViewContainer"], .main {
            overflow-x: hidden !important;
        }

        header[data-testid="stHeader"] {
            background: transparent !important;
        }

        .vf-topbar-shell {
            width: 100%;
            margin: 0 0 1.4rem 0;
            padding: 0;
            border-bottom: 1px solid #e8e8e8;
        }

        .vf-brand {
            font-size: 30px;
            font-weight: 800;
            color: #1f2a44;
            letter-spacing: -0.02em;
            line-height: 1.1;
            white-space: nowrap;
            margin-top: 0.5rem;
            margin-bottom: 0.65rem;
        }

        .vf-nav-btn .stButton > button[kind="tertiary"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #1f2a44 !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            white-space: nowrap !important;
            padding: 0 !important;
            min-height: auto !important;
            line-height: 1.1 !important;
            justify-content: flex-end !important;
        }

        .vf-nav-btn .stButton > button[kind="tertiary"]:hover {
            color: #1f2a44 !important;
            background: transparent !important;
        }

        .vf-nav-btn .stButton > button[kind="tertiary"]:focus,
        .vf-nav-btn .stButton > button[kind="tertiary"]:focus-visible,
        .vf-nav-btn .stButton > button[kind="tertiary"]:active {
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
            background: transparent !important;
        }

        .vf-nav-spacer {
            height: 0.45rem;
        }

        @media (max-width: 900px) {
            .vf-brand {
                font-size: 24px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_top_nav() -> None:
    st.markdown('<div class="vf-topbar-shell">', unsafe_allow_html=True)
    brand_col, spacer_col, nav1, nav2, nav3, nav4 = st.columns([4.8, 2.2, 1.35, 1.55, 0.95, 1.6], gap="small")

    with brand_col:
        st.markdown('<div class="vf-brand">Viabilidade Fácil</div>', unsafe_allow_html=True)

    with nav1:
        st.markdown('<div class="vf-nav-spacer"></div><div class="vf-nav-btn">', unsafe_allow_html=True)
        st.button("Como funciona", key="vf_nav_how", type="tertiary", use_container_width=False)
        st.markdown('</div>', unsafe_allow_html=True)

    with nav2:
        st.markdown('<div class="vf-nav-spacer"></div><div class="vf-nav-btn">', unsafe_allow_html=True)
        if st.button("Área do cliente", key="vf_nav_client", type="tertiary", use_container_width=False):
            st.session_state["show_client_area"] = True
            if not st.session_state.get("auth_logged_in"):
                st.session_state["post_login_action"] = "open_client_area"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with nav3:
        st.markdown('<div class="vf-nav-spacer"></div><div class="vf-nav-btn">', unsafe_allow_html=True)
        st.button("Planos", key="vf_nav_plans", type="tertiary", use_container_width=False)
        st.markdown('</div>', unsafe_allow_html=True)

    with nav4:
        st.markdown('<div class="vf-nav-spacer"></div><div class="vf-nav-btn">', unsafe_allow_html=True)
        st.button("Dúvidas/Suporte", key="vf_nav_support", type="tertiary", use_container_width=False)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def _render_wallet_summary() -> None:
    user_name = st.session_state.get("auth_user_name") or st.session_state.get("auth_name") or "—"
    user_email = st.session_state.get("auth_user_email") or st.session_state.get("auth_email") or "—"
    user_id = st.session_state.get("auth_user_id")

    saldo = "—"
    if user_id:
        try:
            saldo = str(get_credit_balance(user_id))
        except Exception:
            saldo = "—"

    st.markdown("**Minha carteira**")
    c1, c2, c3 = st.columns(3)
    with c1:
        _card("Usuário", user_name)
    with c2:
        _card("E-mail", user_email)
    with c3:
        _card("Saldo de créditos", saldo)


def _render_login_gate_block() -> None:
    render_google_login_box(
        title="Faça login para continuar",
        message="Para liberar a pesquisa de viabilidade, entre com sua conta Google.",
    )


def _render_auth_callback_bridge() -> None:
    code = safe_get_query_param("code") or ""
    error = safe_get_query_param("error") or ""
    error_code = safe_get_query_param("error_code") or ""
    error_description = safe_get_query_param("error_description") or ""
    state = safe_get_query_param("state") or ""
    app_url = get_app_url()

    st.markdown("## Concluindo seu login...")
    st.caption("Aguarde alguns segundos. Se a aba principal não atualizar, ela será redirecionada automaticamente.")

    bridge_html = f"""
    <script>
    (function() {{
        const appUrl = {app_url!r};
        const params = new URLSearchParams();
        const code = {code!r};
        const error = {error!r};
        const errorCode = {error_code!r};
        const errorDescription = {error_description!r};
        const state = {state!r};

        if (code) params.set("code", code);
        if (error) params.set("error", error);
        if (errorCode) params.set("error_code", errorCode);
        if (errorDescription) params.set("error_description", errorDescription);
        if (state) params.set("state", state);

        const destination = params.toString() ? `${appUrl}/?${params.toString()}` : appUrl;

        try {{
            if (window.opener && !window.opener.closed) {{
                window.opener.location.replace(destination);
                window.close();
                return;
            }}
        }} catch (e) {{}}

        window.location.replace(destination);
    }})();
    </script>
    """

    components.html(bridge_html, height=0)
    st.stop()


if "selected_lat" not in st.session_state:
    st.session_state.selected_lat = None
if "selected_lon" not in st.session_state:
    st.session_state.selected_lon = None
if "calc" not in st.session_state or not isinstance(st.session_state.calc, dict):
    st.session_state.calc = {}
st.session_state.calc.setdefault("use_type_code", "RES_UNI")

if "report_unlocked" not in st.session_state:
    st.session_state.report_unlocked = False

if "free_calc_done" not in st.session_state:
    st.session_state.free_calc_done = False

if "last_calc_signature" not in st.session_state:
    st.session_state.last_calc_signature = None

if "show_login_gate" not in st.session_state:
    st.session_state.show_login_gate = False

if "scroll_to_login_gate" not in st.session_state:
    st.session_state.scroll_to_login_gate = False

if "scroll_to_item3" not in st.session_state:
    st.session_state.scroll_to_item3 = False

if "post_login_action" not in st.session_state:
    st.session_state.post_login_action = None

if "show_inline_payments" not in st.session_state:
    st.session_state.show_inline_payments = False

if "show_client_area" not in st.session_state:
    st.session_state.show_client_area = False

if "last_generated_pdf_bytes" not in st.session_state:
    st.session_state.last_generated_pdf_bytes = None

if "last_generated_pdf_signature" not in st.session_state:
    st.session_state.last_generated_pdf_signature = None

if "last_saved_report_signature" not in st.session_state:
    st.session_state.last_saved_report_signature = None

if "report_snapshot_calc" not in st.session_state:
    st.session_state.report_snapshot_calc = None
if "report_snapshot_session" not in st.session_state:
    st.session_state.report_snapshot_session = None
if "report_snapshot_signature" not in st.session_state:
    st.session_state.report_snapshot_signature = None
if "confirm_new_report" not in st.session_state:
    st.session_state.confirm_new_report = False
if "pending_report_calc" not in st.session_state:
    st.session_state.pending_report_calc = None
if "pending_report_session" not in st.session_state:
    st.session_state.pending_report_session = None
if "pending_report_signature" not in st.session_state:
    st.session_state.pending_report_signature = None

# Se esta aba for a popup de callback, ela só devolve o retorno do Google para a aba principal.
if safe_get_query_param("auth_flow") == "callback":
    _render_auth_callback_bridge()

# O exchange do code deve acontecer na aba principal.
handle_oauth_callback()

_inject_global_styles()

if safe_get_query_param("nav") == "client":
    st.session_state["show_client_area"] = True
    try:
        st.query_params.clear()
    except Exception:
        pass

if st.session_state.get("auth_logged_in") and st.session_state.get("post_login_action") == "open_client_area":
    st.session_state["show_client_area"] = True
    st.session_state["post_login_action"] = None

zones_gj = _zones_geojson()
zones_prepared = _zones_prepared()

user_logged_in = bool(st.session_state.get("auth_logged_in"))
user_id = st.session_state.get("auth_user_id")
user_email = st.session_state.get("auth_user_email")
user_name = st.session_state.get("auth_user_name") or st.session_state.get("auth_name") or "—"

_render_top_nav()

if st.session_state.get("show_client_area"):
    if user_logged_in and user_id:
        saldo_cliente = None
        try:
            saldo_cliente = get_credit_balance(user_id)
        except Exception:
            saldo_cliente = None
        if st.button("← Voltar para o estudo", key="client_area_back"):
            st.session_state["show_client_area"] = False
            st.rerun()
        render_client_area_page(
            user_id=user_id,
            user_name=user_name,
            user_email=user_email or "—",
            credit_balance=saldo_cliente,
        )
    else:
        if st.button("← Voltar para o estudo", key="client_area_back_guest"):
            st.session_state["show_client_area"] = False
            st.rerun()
        st.markdown("## Área do cliente")
        st.info("Faça login com Google para acessar sua área do cliente e ver seus relatórios salvos.")
        _render_login_gate_block()
    st.stop()

if user_logged_in and user_id and user_email:
    reconcile_key = f"{user_id}:{user_email}"
    if st.session_state.get("wallet_reconcile_done_for") != reconcile_key:
        try:
            reconcile_result = reconcile_wallet_to_current_user(user_id, user_email)
            st.session_state["wallet_reconcile_done_for"] = reconcile_key
            st.session_state["wallet_reconcile_result"] = reconcile_result
        except Exception as e:
            st.session_state["wallet_reconcile_error"] = str(e)

st.title("Viabilidade Urbana")
st.caption("Selecione o terreno, faça a análise inicial e gere o relatório completo quando quiser.")

right_col_left, right_col_right = st.columns([2.2, 1.2], gap="large")
with right_col_left:
    st.write("")

with right_col_right:
    if user_logged_in and user_id:
        _render_wallet_summary()
        render_google_login_top()
    else:
        render_google_login_top()

with st.sidebar:
    st.markdown("### 📋 1. Escolha o Uso")

    categoria_label = st.selectbox(
        "Categoria:",
        options=[
            "Residencial",
            "Comercial (Em breve)",
            "Serviço (Em breve)",
            "Saúde/Educação (Em breve)",
        ],
        index=0,
        key="vf_categoria",
    )

    residential_options = {
        "Residencial Unifamiliar (Casa)": ("RES_UNI", ""),
        "Multifamiliar R2.1 (2 unidades no mesmo lote)": ("RES_MULTI_R21", "R21"),
        "Multifamiliar R2.2 (condomínio horizontal com via interna)": ("RES_MULTI_R22", "R22"),
        "Multifamiliar R3 (condomínio vertical / prédio)": ("RES_MULTI_R3", "R3"),
    }

    selected_use_label = st.selectbox(
        "Opções na Categoria:",
        options=list(residential_options.keys()),
        index=0,
        key="vf_residential_option",
        disabled=(categoria_label != "Residencial"),
    )

    selected_use_code, selected_multi_tipo = residential_options.get(selected_use_label, ("RES_UNI", ""))
    st.session_state.calc["use_type_code"] = selected_use_code

    if selected_use_code.startswith("RES_MULTI_"):
        st.session_state.calc["project_mode"] = "GUIA_FASE_1"
        st.session_state.calc["multi_tipo"] = selected_multi_tipo
    else:
        st.session_state.calc.pop("project_mode", None)
        st.session_state.calc.pop("multi_tipo", None)

    if categoria_label != "Residencial":
        st.caption("Essa categoria ficará disponível em breve.")

    st.markdown('<div class="vf-side-divider"></div>', unsafe_allow_html=True)

    st.markdown("### 🔎 2. Busca Direta")
    st.text_input(
        "Ou digite para pesquisar:",
        value="Em breve",
        disabled=True,
        key="vf_busca_direta",
    )
    st.caption("A busca direta ficará disponível em breve.")

    st.markdown('<div class="vf-side-divider"></div>', unsafe_allow_html=True)

    st.markdown("### 📐 3. Dados do Lote")
    st.caption("Mantido o bloco funcional já consolidado, incluindo a lógica de terreno irregular.")

    lot_area, built_ground, permeable_area = render_lote_section()

st.markdown(
    '<div class="vf-section-title">📍 Selecione o lote no mapa:</div>',
    unsafe_allow_html=True,
)

radius_m = render_mapa_section(zones_gj)

def _current_report_session_snapshot(calc_ref, built_ground_value, permeable_area_value):
    return {
        "lot_area_m2": calc_ref.get("lot_area_m2"),
        "built_ground_m2": built_ground_value,
        "permeable_area_m2": permeable_area_value,
        "lot_front_m": calc_ref.get("lot_front_m"),
        "lot_depth_m": calc_ref.get("lot_depth_m"),
        "lot_is_corner": calc_ref.get("lot_is_corner"),
        "lot_is_midblock": calc_ref.get("lot_is_midblock"),
        "lot_is_irregular": bool(st.session_state.get("lot_is_irregular", False)),
    }


def _commit_report_snapshot(calc_ref, session_snapshot, pdf_bytes, signature):
    st.session_state.report_snapshot_calc = deepcopy(calc_ref)
    st.session_state.report_snapshot_session = deepcopy(session_snapshot)
    st.session_state.report_snapshot_signature = signature
    st.session_state.last_generated_pdf_bytes = pdf_bytes
    st.session_state.last_generated_pdf_signature = signature
    st.session_state.report_unlocked = True
    st.session_state.show_inline_payments = False


def _clear_pending_report():
    st.session_state.confirm_new_report = False
    st.session_state.pending_report_calc = None
    st.session_state.pending_report_session = None
    st.session_state.pending_report_signature = None


def _clear_report_runtime_state(*, clear_last_calc_signature: bool = False) -> None:
    st.session_state.report_unlocked = False
    st.session_state.show_inline_payments = False
    st.session_state.last_generated_pdf_bytes = None
    st.session_state.last_generated_pdf_signature = None
    st.session_state.last_saved_report_signature = None
    st.session_state.report_snapshot_calc = None
    st.session_state.report_snapshot_session = None
    st.session_state.report_snapshot_signature = None
    _clear_pending_report()
    if clear_last_calc_signature:
        st.session_state.last_calc_signature = None


def _should_block_report_preview(calc_ref: Dict[str, Any]) -> bool:
    if not isinstance(calc_ref, dict):
        return False
    if not calc_ref.get("ok") or not calc_ref.get("rule") or not (calc_ref.get("zone") or calc_ref.get("zone_sigla")) or calc_ref.get("err"):
        return False
    if str(calc_ref.get("use_type_code") or "").startswith("RES_MULTI_") and calc_ref.get("project_mode") == "GUIA_FASE_1":
        return should_block_multifamiliar_preview(calc_ref, rule=calc_ref.get("rule") or {})
    return should_block_unifamiliar_preview(calc_ref)


def _render_blocked_report_preview(calc_ref: Dict[str, Any]) -> None:
    rule_ref = calc_ref.get("rule") or {}
    if str(calc_ref.get("use_type_code") or "").startswith("RES_MULTI_") and calc_ref.get("project_mode") == "GUIA_FASE_1":
        render_multifamiliar_inadequado_preview(calc=calc_ref, rule=rule_ref)
    else:
        render_unifamiliar_inadequado_preview(calc_ref)


def _prepare_and_consume_report(calc_ref, session_snapshot, report_signature, user_id_value, selected_use_label_value, categoria_label_value):
    pdf_bytes = generate_report_pdf_bytes(calc=calc_ref, session_state=session_snapshot)
    debit_result = consume_viability_credit(
        user_id=user_id_value,
        amount=1,
        description="Geração de relatório de viabilidade",
    )
    if not debit_result.get("ok"):
        raise RuntimeError(debit_result.get("message") or "Saldo insuficiente para gerar o relatório.")
    _commit_report_snapshot(calc_ref, session_snapshot, pdf_bytes, report_signature)
    try:
        if st.session_state.get("last_saved_report_signature") != report_signature:
            save_result = save_client_report(
                user_id=user_id_value,
                user_email=st.session_state.get("auth_user_email") or "",
                calc={**calc_ref, "selected_use_label": selected_use_label_value, "categoria_label": categoria_label_value},
                session_state=session_snapshot,
                pdf_bytes=pdf_bytes,
                report_signature=report_signature,
            )
            if save_result.get("ok"):
                st.session_state.last_saved_report_signature = report_signature
    except Exception:
        pass
    return debit_result, pdf_bytes


btn_col1, btn_col2, btn_col3 = st.columns([1, 2.1, 1])
with btn_col2:
    clicked_calcular = st.button(
        "🚀 GERAR ESTUDO DE VIABILIDADE",
        key="btn_calc",
        use_container_width=True,
    )

    limpar_tudo = st.button(
        "🗑️ LIMPAR TUDO",
        key="btn_clear_all",
        use_container_width=True,
    )

    if limpar_tudo:
        st.session_state.selected_lat = None
        st.session_state.selected_lon = None
        st.session_state.calc = {"use_type_code": st.session_state.calc.get("use_type_code", "RES_UNI")}
        _clear_report_runtime_state(clear_last_calc_signature=True)
        st.session_state.free_calc_done = False
        st.session_state.show_login_gate = False
        st.session_state.scroll_to_login_gate = False
        st.session_state.scroll_to_item3 = False
        st.session_state.post_login_action = None
        st.session_state.show_inline_payments = False
        st.rerun()

st.session_state.calc["lot_area_m2"] = float(lot_area)
st.session_state.calc["lot_front_m"] = float(st.session_state.get("lot_front_m") or 0.0)
st.session_state.calc["lot_depth_m"] = float(st.session_state.get("lot_depth_m") or 0.0)
st.session_state.calc["lot_is_corner"] = bool(st.session_state.get("lot_is_corner", False))
st.session_state.calc["lot_is_midblock"] = bool(st.session_state.get("lot_is_midblock", not st.session_state.calc["lot_is_corner"]))

current_signature = json.dumps(
    {
        "lat": st.session_state.get("selected_lat"),
        "lon": st.session_state.get("selected_lon"),
        "lot_area_m2": st.session_state.calc.get("lot_area_m2"),
        "lot_front_m": st.session_state.calc.get("lot_front_m"),
        "lot_depth_m": st.session_state.calc.get("lot_depth_m"),
        "lot_is_corner": st.session_state.calc.get("lot_is_corner"),
        "lot_is_midblock": st.session_state.calc.get("lot_is_midblock"),
        "use_type_code": st.session_state.calc.get("use_type_code"),
        "categoria_label": categoria_label,
    },
    sort_keys=True,
    default=str,
)

if st.session_state.last_calc_signature and st.session_state.last_calc_signature != current_signature:
    _clear_report_runtime_state()
    st.session_state.free_calc_done = False
    st.session_state.calc.pop("err", None)
    st.session_state.calc.pop("rule", None)

calc = st.session_state.calc
user_logged_in = bool(st.session_state.get("auth_logged_in"))
user_id = st.session_state.get("auth_user_id")
user_email = st.session_state.get("auth_user_email")

if user_logged_in and user_id and user_email:
    reconcile_key = f"{user_id}:{user_email}"
    if st.session_state.get("wallet_reconcile_done_for") != reconcile_key:
        try:
            reconcile_result = reconcile_wallet_to_current_user(user_id, user_email)
            st.session_state["wallet_reconcile_done_for"] = reconcile_key
            st.session_state["wallet_reconcile_result"] = reconcile_result
        except Exception as e:
            st.session_state["wallet_reconcile_error"] = str(e)

st.markdown('<div id="login-gate-start"></div>', unsafe_allow_html=True)

run_free_calc_now = False

if clicked_calcular:
    if categoria_label != "Residencial":
        st.info("Essa categoria ainda está em desenvolvimento. Use Residencial por enquanto.")
    else:
        if not user_logged_in or not user_id:
            st.session_state.show_login_gate = True
            st.session_state.scroll_to_login_gate = True
            st.session_state.post_login_action = "calculate_viability"
        else:
            st.session_state.show_login_gate = False
            st.session_state.show_inline_payments = False
            run_free_calc_now = True
            st.session_state.scroll_to_item3 = True

if (
    st.session_state.get("post_login_action") == "calculate_viability"
    and user_logged_in
    and user_id
    and categoria_label == "Residencial"
):
    run_free_calc_now = True
    st.session_state.post_login_action = None
    st.session_state.show_login_gate = False
    st.session_state.scroll_to_item3 = True

if st.session_state.get("show_login_gate") and not (user_logged_in and user_id):
    _render_login_gate_block()
    st.divider()

st.markdown('<div id="item-3-start"></div>', unsafe_allow_html=True)

show_item3 = bool(run_free_calc_now or st.session_state.get("free_calc_done"))

if run_free_calc_now:
    _clear_report_runtime_state()
    st.session_state.free_calc_done = False
    st.session_state.last_calc_signature = current_signature

    calc.pop("err", None)
    calc.pop("rule", None)

    _ = render_localizacao_section(True, zones_prepared, radius_m)

    if calc.get("zone") and not calc.get("rule"):
        try:
            rule = fetch_rule(calc.get("zone_sigla") or calc["zone"], calc.get("use_type_code") or "RES_UNI", calc.get("subzone_code") or "PADRAO", calc.get("zone_label_raw") or calc.get("zone"))
            if rule:
                calc["rule"] = rule
                st.session_state.free_calc_done = True
            else:
                calc["err"] = (
                    f"Nenhuma regra no Supabase para zona={calc['zone']} "
                    f"e uso={calc.get('use_type_code')}"
                )
        except Exception as e:
            calc["err"] = f"Erro ao consultar Supabase: {e}"

elif show_item3:
    _ = render_localizacao_section(False, zones_prepared, radius_m)

section4_can_try = bool(calc.get("zone") or calc.get("zone_sigla") or calc.get("zone_lookup")) and bool(calc.get("use_type_code"))

if section4_can_try:
    render_indices_section(
        calc=calc,
        card_func=_card,
        pick_func=pick_rule,
        get_rule_func=fetch_rule,
    )
    if calc.get("rule"):
        st.session_state.free_calc_done = True



preview_inadequado = _should_block_report_preview(calc)
if preview_inadequado:
    _clear_report_runtime_state()
    st.markdown("---")
    _render_blocked_report_preview(calc)

can_offer_report = bool(calc.get("rule")) and bool(calc.get("zone")) and not bool(calc.get("err")) and not preview_inadequado

if can_offer_report:
    st.markdown("---")
    st.subheader("Relatório completo")
    st.caption(
        "A análise inicial acima é gratuita. Para liberar o relatório completo, "
        "gere o relatório com 1 crédito."
    )

    current_report_session = _current_report_session_snapshot(calc, built_ground, permeable_area)
    current_report_signature = build_report_signature(calc=calc, session_state=current_report_session)
    snapshot_signature = st.session_state.get("report_snapshot_signature")
    has_snapshot = bool(st.session_state.get("report_snapshot_calc")) and bool(snapshot_signature)
    is_same_as_snapshot = bool(has_snapshot and snapshot_signature == current_report_signature)

    saldo_atual = None
    if user_logged_in and user_id:
        try:
            saldo_atual = get_credit_balance(user_id)
        except Exception:
            saldo_atual = None

    c1, c2 = st.columns([1, 2])

    with c1:
        gerar_relatorio = st.button(
            "📄 Gerar relatório",
            key="btn_generate_report",
            use_container_width=True,
            disabled=(not user_logged_in),
        )

    with c2:
        if not user_logged_in:
            st.info("Faça login com Google para gerar o relatório completo.")
        else:
            if saldo_atual is not None:
                st.info(f"Saldo atual: {saldo_atual} crédito(s).")
            else:
                st.info("Não foi possível consultar o saldo neste momento.")

    if gerar_relatorio:
        if preview_inadequado:
            _clear_report_runtime_state()
            st.error("Este estudo está bloqueado por inadequabilidade. O crédito foi preservado.")
        elif not user_logged_in or not user_id:
            st.error("Faça login com Google para gerar o relatório completo.")
        elif has_snapshot and not is_same_as_snapshot:
            st.session_state.confirm_new_report = True
            st.session_state.pending_report_calc = deepcopy(calc)
            st.session_state.pending_report_session = deepcopy(current_report_session)
            st.session_state.pending_report_signature = current_report_signature
            st.rerun()
        elif is_same_as_snapshot:
            st.info("Este relatório já foi gerado e continua disponível abaixo.")
        elif saldo_atual is not None and int(saldo_atual) <= 0:
            st.session_state.show_inline_payments = True
            st.error("Você não possui créditos suficientes para gerar o relatório.")
        else:
            try:
                debit_result, _ = _prepare_and_consume_report(
                    calc_ref=deepcopy(calc),
                    session_snapshot=deepcopy(current_report_session),
                    report_signature=current_report_signature,
                    user_id_value=user_id,
                    selected_use_label_value=selected_use_label,
                    categoria_label_value=categoria_label,
                )
                novo_saldo = debit_result.get("new_balance")
                st.success(f"1 crédito consumido com sucesso. Saldo atual: {novo_saldo}")
                _clear_pending_report()
                st.rerun()
            except Exception as e:
                st.session_state.show_inline_payments = True
                st.error(f"Não foi possível preparar e gerar o relatório: {e}")

    if has_snapshot and not is_same_as_snapshot:
        st.warning(
            "Você está visualizando um relatório já gerado. Para gerar outro relatório neste novo cenário, confirme antes. Isso gastará outro crédito."
        )

    if st.session_state.get("confirm_new_report") and st.session_state.get("pending_report_signature") == current_report_signature:
        st.warning("Você tem certeza que deseja gerar outro relatório? Isso vai gastar outro crédito.")
        c_yes, c_no = st.columns(2)
        with c_yes:
            confirm_yes = st.button("Sim, gerar outro relatório", key="btn_confirm_new_report_yes", use_container_width=True)
        with c_no:
            confirm_no = st.button("Não", key="btn_confirm_new_report_no", use_container_width=True)

        if confirm_no:
            _clear_pending_report()
            st.rerun()

        if confirm_yes:
            if preview_inadequado:
                _clear_report_runtime_state()
                st.error("Este estudo está bloqueado por inadequabilidade. O crédito foi preservado.")
            else:
                try:
                    pending_calc = deepcopy(st.session_state.get("pending_report_calc") or calc)
                    pending_session = deepcopy(st.session_state.get("pending_report_session") or current_report_session)
                    pending_sig = st.session_state.get("pending_report_signature") or current_report_signature
                    debit_result, _ = _prepare_and_consume_report(
                        calc_ref=pending_calc,
                        session_snapshot=pending_session,
                        report_signature=pending_sig,
                        user_id_value=user_id,
                        selected_use_label_value=selected_use_label,
                        categoria_label_value=categoria_label,
                    )
                    novo_saldo = debit_result.get("new_balance")
                    st.success(f"1 crédito consumido com sucesso. Saldo atual: {novo_saldo}")
                    _clear_pending_report()
                    st.rerun()
                except Exception as e:
                    st.session_state.show_inline_payments = True
                    st.error(f"Não foi possível preparar e gerar o novo relatório: {e}")

    if st.session_state.get("show_inline_payments"):
        st.markdown("### Comprar créditos")
        render_payments_panel()

if (st.session_state.get("report_snapshot_calc") and st.session_state.get("report_snapshot_signature")) and can_offer_report:
    st.markdown("---")
    report_calc = deepcopy(st.session_state.get("report_snapshot_calc"))
    report_session = deepcopy(st.session_state.get("report_snapshot_session") or {})

    render_analise_section(
        report_calc,
        lot_area=report_session.get("lot_area_m2", lot_area),
        built_ground=report_session.get("built_ground_m2", built_ground),
        permeable_area=report_session.get("permeable_area_m2", permeable_area),
        pick_func=pick_rule,
    )

    render_zone_description_section(report_calc)
    render_relatorio_section(report_calc)

    st.markdown("### Download do relatório")
    try:
        pdf_bytes = st.session_state.get("last_generated_pdf_bytes")
        if not pdf_bytes or st.session_state.get("last_generated_pdf_signature") != st.session_state.get("report_snapshot_signature"):
            pdf_bytes = generate_report_pdf_bytes(calc=report_calc, session_state=report_session)
            st.session_state["last_generated_pdf_bytes"] = pdf_bytes
            st.session_state["last_generated_pdf_signature"] = st.session_state.get("report_snapshot_signature")

        st.download_button(
            label="⬇️ Baixar relatório em PDF",
            data=pdf_bytes,
            file_name="relatorio_viabilidade.pdf",
            mime="application/pdf",
            key="download_report_pdf",
            use_container_width=True,
        )
    except Exception as e:
        st.error(f"Falha ao preparar o PDF para download: {e}")


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
