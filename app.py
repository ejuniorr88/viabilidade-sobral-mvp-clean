import json
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
from ui.relatorio import render_relatorio_section
from core.auth import handle_oauth_callback, get_app_url, safe_get_query_param
from ui.auth_panel import render_google_login_top, render_google_login_box
from ui.payments_panel import render_payments_panel
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
        }

        .vf-topbar {
            width: 100%;
            background: #ffffff;
            border-bottom: 1px solid #e8e8e8;
        }

        .vf-topbar-inner {
            width: 100%;
            min-height: 76px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
            padding: 0 18px;
            box-sizing: border-box;
        }

        .vf-brand {
            font-size: 30px;
            font-weight: 800;
            color: #1f2a44;
            letter-spacing: -0.02em;
            line-height: 1.1;
            white-space: nowrap;
        }

        .vf-brand-link {
            text-decoration: none !important;
            color: #1f2a44 !important;
        }

        .vf-links {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 26px;
            flex-wrap: wrap;
        }

        .vf-link {
            color: #1f2a44;
            text-decoration: none;
            font-weight: 600;
            font-size: 15px;
            white-space: nowrap;
        }

        .vf-main-title-wrap {
            width: 100%;
            text-align: center;
            margin-top: 0.6rem;
            margin-bottom: 0.2rem;
        }

        .vf-main-title {
            font-size: 42px;
            font-weight: 800;
            color: #1f2a44;
            letter-spacing: -0.02em;
            line-height: 1.1;
            margin: 0;
        }

        .vf-main-subtitle {
            margin-top: 10px;
            margin-bottom: 0.8rem;
            font-size: 15px;
            color: #6b7280;
            text-align: center;
        }

        .vf-section-title {
            font-size: 26px;
            font-weight: 800;
            color: #24324a;
            margin-bottom: 12px;
        }

        .vf-wallet-wrap {
            margin-top: 0;
            margin-bottom: 14px;
        }

        .vf-wallet-title {
            font-size: 18px;
            font-weight: 800;
            color: #24324a;
            margin-bottom: 10px;
        }

        .vf-wallet-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 10px;
        }

        .vf-wallet-card {
            background: #ffffff;
            border: 1px solid #e8e8e8;
            border-radius: 14px;
            padding: 12px 14px;
            min-height: 84px;
        }

        .vf-wallet-label {
            font-size: 12px;
            color: #6b7280;
            margin-bottom: 6px;
        }

        .vf-wallet-value {
            font-size: 17px;
            font-weight: 700;
            color: #1f2a44;
            word-break: break-word;
            line-height: 1.25;
        }

        section[data-testid="stSidebar"] {
            background: #eef0f3;
            border-right: 1px solid #d9dee5;
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 1.5rem !important;
        }

        .vf-side-divider {
            border-top: 1px solid #cfd5dd;
            margin: 16px 0 18px 0;
        }

        @media (max-width: 1100px) {
            .vf-topbar-inner {
                flex-direction: column;
                align-items: flex-start;
                justify-content: center;
                padding-top: 14px;
                padding-bottom: 14px;
            }

            .vf-links {
                justify-content: flex-start;
                gap: 18px;
            }

            .vf-wallet-grid {
                grid-template-columns: 1fr;
            }

            .vf-main-title {
                font-size: 34px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_top_nav() -> None:
    st.markdown(
        """
        <div class="vf-topbar-shell">
          <div class="vf-topbar">
            <div class="vf-topbar-inner">
              <a class="vf-brand vf-brand-link" href="?page=home">Viabilidade Fácil</a>
              <div class="vf-links">
                <a class="vf-link" href="#">Como funciona</a>
                <a class="vf-link" href="?page=client">Área do cliente</a>
                <a class="vf-link" href="#">Planos</a>
                <a class="vf-link" href="#">Dúvidas/Suporte</a>
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )



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

requested_page = safe_get_query_param("page") or ""
if requested_page == "client":
    st.session_state.show_client_area = True
elif requested_page == "home":
    st.session_state.show_client_area = False

if "last_generated_pdf_bytes" not in st.session_state:
    st.session_state.last_generated_pdf_bytes = None

if "last_generated_pdf_signature" not in st.session_state:
    st.session_state.last_generated_pdf_signature = None

if "last_saved_report_signature" not in st.session_state:
    st.session_state.last_saved_report_signature = None

# Se esta aba for a popup de callback, ela só devolve o retorno do Google para a aba principal.
if safe_get_query_param("auth_flow") == "callback":
    _render_auth_callback_bridge()

# O exchange do code deve acontecer na aba principal.
handle_oauth_callback()

zones_gj = _zones_geojson()
zones_prepared = _zones_prepared()

user_logged_in = bool(st.session_state.get("auth_logged_in"))
user_id = st.session_state.get("auth_user_id")
user_email = st.session_state.get("auth_user_email")
user_name = st.session_state.get("auth_user_name") or st.session_state.get("auth_name") or "—"

if st.session_state.get("show_client_area"):
    if user_logged_in and user_id:
        saldo_cliente = None
        try:
            saldo_cliente = get_credit_balance(user_id)
        except Exception:
            saldo_cliente = None
        if st.button("← Voltar para o estudo", key="client_area_back"):
            st.session_state["show_client_area"] = False
            st.query_params["page"] = "home"
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
            st.query_params["page"] = "home"
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

_inject_global_styles()
_render_top_nav()

st.markdown('<div class="vf-main-title-wrap"><h1 class="vf-main-title">Viabilidade Urbana</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="vf-main-subtitle">Selecione o terreno, faça a análise inicial e gere o relatório completo quando quiser.</div>', unsafe_allow_html=True)

right_col_left, right_col_right = st.columns([2.2, 1.2], gap="large")
with right_col_left:
    st.write("")

with right_col_right:
    if user_logged_in and user_id:
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
        st.session_state.report_unlocked = False
        st.session_state.free_calc_done = False
        st.session_state.last_calc_signature = None
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

current_signature = json.dumps(
    {
        "lat": st.session_state.get("selected_lat"),
        "lon": st.session_state.get("selected_lon"),
        "lot_area_m2": st.session_state.calc.get("lot_area_m2"),
        "lot_front_m": st.session_state.calc.get("lot_front_m"),
        "lot_depth_m": st.session_state.calc.get("lot_depth_m"),
        "lot_is_corner": st.session_state.calc.get("lot_is_corner"),
        "use_type_code": st.session_state.calc.get("use_type_code"),
        "categoria_label": categoria_label,
    },
    sort_keys=True,
    default=str,
)

if st.session_state.last_calc_signature and st.session_state.last_calc_signature != current_signature:
    st.session_state.report_unlocked = False
    st.session_state.free_calc_done = False
    st.session_state.show_inline_payments = False
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
    st.session_state.report_unlocked = False
    st.session_state.free_calc_done = False
    st.session_state.last_calc_signature = current_signature
    st.session_state.show_inline_payments = False

    calc.pop("err", None)
    calc.pop("rule", None)

    _ = render_localizacao_section(True, zones_prepared, radius_m)

    if calc.get("zone") and not calc.get("rule"):
        try:
            rule = fetch_rule(calc["zone"], calc.get("use_type_code") or "RES_UNI")
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

if st.session_state.get("free_calc_done"):
    render_indices_section(
        calc=calc,
        card_func=_card,
        pick_func=pick_rule,
        get_rule_func=fetch_rule,
    )

can_offer_report = bool(st.session_state.get("free_calc_done")) and bool(calc.get("zone")) and not bool(calc.get("err"))

if can_offer_report:
    st.markdown("---")
    st.subheader("Relatório completo")
    st.caption(
        "A análise inicial acima é gratuita. Para liberar o relatório completo, "
        "gere o relatório com 1 crédito."
    )

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
        if not user_logged_in or not user_id:
            st.error("Faça login com Google para gerar o relatório completo.")
        elif saldo_atual is not None and int(saldo_atual) <= 0:
            st.session_state.show_inline_payments = True
            st.session_state.report_unlocked = False
            st.error("Você não possui créditos suficientes para gerar o relatório.")
        else:
            try:
                debit_result = consume_viability_credit(
                    user_id=user_id,
                    amount=1,
                    description="Geração de relatório de viabilidade",
                )

                if not debit_result.get("ok"):
                    st.session_state.show_inline_payments = True
                    st.session_state.report_unlocked = False
                    st.error(
                        debit_result.get("message")
                        or "Saldo insuficiente para gerar o relatório."
                    )
                else:
                    st.session_state.show_inline_payments = False
                    st.session_state.report_unlocked = True
                    novo_saldo = debit_result.get("new_balance")
                    st.success(f"1 crédito consumido com sucesso. Saldo atual: {novo_saldo}")
                    st.rerun()

            except Exception as e:
                st.session_state.show_inline_payments = True
                st.session_state.report_unlocked = False
                st.error(f"Não foi possível descontar o crédito: {e}")

    if st.session_state.get("show_inline_payments"):
        st.markdown("### Comprar créditos")
        render_payments_panel()

if st.session_state.get("report_unlocked") and can_offer_report:
    st.markdown("---")

    render_analise_section(
        calc,
        lot_area=lot_area,
        built_ground=built_ground,
        permeable_area=permeable_area,
        pick_func=pick_rule,
    )

    render_relatorio_section(calc)

    st.markdown("### Download do relatório")
    try:
        pdf_bytes = generate_report_pdf_bytes(
            calc=calc,
            session_state={
                "lot_area_m2": st.session_state.calc.get("lot_area_m2"),
                "built_ground_m2": built_ground,
                "permeable_area_m2": permeable_area,
                "lot_front_m": st.session_state.calc.get("lot_front_m"),
                "lot_depth_m": st.session_state.calc.get("lot_depth_m"),
                "lot_is_corner": st.session_state.calc.get("lot_is_corner"),
                "lot_is_irregular": bool(st.session_state.get("lot_is_irregular", False)),
            },
        )

        st.session_state["last_generated_pdf_bytes"] = pdf_bytes
        current_report_signature = build_report_signature(
            calc=calc,
            session_state={
                "lot_area_m2": st.session_state.calc.get("lot_area_m2"),
                "lot_front_m": st.session_state.calc.get("lot_front_m"),
                "lot_depth_m": st.session_state.calc.get("lot_depth_m"),
                "lot_is_corner": st.session_state.calc.get("lot_is_corner"),
                "lot_is_irregular": bool(st.session_state.get("lot_is_irregular", False)),
            },
        )
        st.session_state["last_generated_pdf_signature"] = current_report_signature

        st.download_button(
            label="⬇️ Baixar relatório em PDF",
            data=pdf_bytes,
            file_name="relatorio_viabilidade.pdf",
            mime="application/pdf",
            key="download_report_pdf",
            use_container_width=True,
        )

        if st.session_state.get("last_saved_report_signature") != current_report_signature:
            try:
                save_result = save_client_report(
                    user_id=user_id,
                    user_email=st.session_state.get("auth_user_email") or "",
                    calc={
                        **calc,
                        "selected_use_label": selected_use_label,
                        "categoria_label": categoria_label,
                    },
                    session_state={
                        "lot_area_m2": st.session_state.calc.get("lot_area_m2"),
                        "lot_front_m": st.session_state.calc.get("lot_front_m"),
                        "lot_depth_m": st.session_state.calc.get("lot_depth_m"),
                        "lot_is_corner": st.session_state.calc.get("lot_is_corner"),
                        "lot_is_irregular": bool(st.session_state.get("lot_is_irregular", False)),
                    },
                    pdf_bytes=pdf_bytes,
                    report_signature=current_report_signature,
                )
                st.session_state["last_saved_report_signature"] = current_report_signature
                if save_result.get("already_exists"):
                    st.info("Este relatório já estava salvo automaticamente na sua área do cliente.")
                else:
                    st.success("Relatório salvo automaticamente na sua área do cliente.")
            except Exception as e:
                st.error(f"Não foi possível salvar automaticamente o relatório na área do cliente: {e}")
        else:
            st.caption("Este relatório já está salvo na sua área do cliente.")
    except Exception as e:
        st.error(f"Não foi possível gerar o PDF do relatório: {e}")

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
