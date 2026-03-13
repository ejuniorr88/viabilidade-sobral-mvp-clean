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
from core.credits import consume_viability_credit, get_credit_balance
from core.report_pdf import generate_report_pdf_bytes


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
                width: 100%;
                justify-content: flex-start;
                gap: 18px;
            }

            .vf-main-title {
                font-size: 34px;
            }

            .vf-wallet-grid {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 640px) {
            .vf-brand {
                font-size: 24px;
            }

            .vf-main-title {
                font-size: 28px;
            }

            .vf-main-subtitle {
                font-size: 14px;
                line-height: 1.45;
                padding: 0 6px;
            }

            .vf-link {
                font-size: 14px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_topbar() -> None:
    st.markdown(
        """
        <div class="vf-topbar-shell">
            <div class="vf-topbar">
                <div class="vf-topbar-inner">
                    <div class="vf-brand">Viabilidade Fácil</div>
                    <div class="vf-links">
                        <a class="vf-link" href="#como-funciona">Como funciona</a>
                        <a class="vf-link" href="#area-do-cliente">Área do cliente</a>
                        <a class="vf-link" href="#planos">Planos</a>
                        <a class="vf-link" href="#duvidas-suporte">Dúvidas/Suporte</a>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_main_title() -> None:
    st.markdown(
        """
        <div class="vf-main-title-wrap">
            <h1 class="vf-main-title">Viabilidade Fácil</h1>
            <div class="vf-main-subtitle">
                Selecione o terreno, faça a análise inicial e gere o relatório completo quando quiser.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value in (1, "1", "true", "True", "sim", "yes", "on"):
        return True
    return False


def _get_calc_context() -> Dict[str, Any]:
    return st.session_state.setdefault("calc", {})


def _set_calc_context(data: Dict[str, Any]) -> None:
    st.session_state["calc"] = data


def _set_defaults() -> None:
    defaults = {
        "auth_logged_in": False,
        "auth_user_id": None,
        "auth_user_email": None,
        "auth_user_name": None,
        "auth_message": None,
        "auth_last_error": None,
        "oauth_url": None,
        "calc": {},
        "report_unlocked": False,
        "show_inline_payments": False,
        "scroll_to_login_gate": False,
        "scroll_to_item3": False,
        "lot_is_irregular": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _get_user_name_or_email() -> str:
    return (
        st.session_state.get("auth_user_name")
        or st.session_state.get("auth_user_email")
        or "Usuário"
    )


def _render_wallet_block() -> None:
    user_id = st.session_state.get("auth_user_id")
    email = st.session_state.get("auth_user_email")
    if not user_id:
        return

    balance = get_credit_balance(user_id)

    st.markdown('<div id="area-do-cliente"></div>', unsafe_allow_html=True)
    st.markdown('<div class="vf-wallet-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="vf-wallet-title">Minha carteira</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="vf-wallet-grid">
            <div class="vf-wallet-card">
                <div class="vf-wallet-label">Usuário</div>
                <div class="vf-wallet-value">{_get_user_name_or_email()}</div>
            </div>
            <div class="vf-wallet-card">
                <div class="vf-wallet-label">E-mail</div>
                <div class="vf-wallet-value">{email or "—"}</div>
            </div>
            <div class="vf-wallet-card">
                <div class="vf-wallet-label">Saldo de créditos</div>
                <div class="vf-wallet-value">{balance}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def _reset_report_gate() -> None:
    st.session_state.report_unlocked = False
    st.session_state.show_inline_payments = False


def _ensure_sidebar_anchor() -> None:
    with st.sidebar:
        st.markdown('<div id="como-funciona"></div>', unsafe_allow_html=True)
        st.markdown("### Informações iniciais")
        st.markdown(
            """
            Este sistema ajuda na leitura inicial de viabilidade urbana.
            Preencha os dados do lote, faça a análise e, se quiser,
            gere o relatório completo ao final.
            """
        )
        st.markdown('<div class="vf-side-divider"></div>', unsafe_allow_html=True)


def _render_login_gate_box() -> None:
    st.markdown('<div id="login-gate-start"></div>', unsafe_allow_html=True)
    st.markdown("### Entre para continuar")
    st.info(
        "Para liberar a geração do relatório e acessar sua carteira, entre com sua conta Google."
    )
    render_google_login_box()


def _offer_report_gate(can_offer_report: bool) -> None:
    if not can_offer_report:
        return

    user_id = st.session_state.get("auth_user_id")
    logged_in = bool(st.session_state.get("auth_logged_in") and user_id)

    if not logged_in:
        st.session_state.scroll_to_login_gate = True
        st.warning("Você precisa entrar para liberar o relatório completo.")
        return

    current_balance = get_credit_balance(user_id)
    if current_balance <= 0:
        st.session_state.show_inline_payments = True
        st.warning("Você está sem créditos. Escolha um plano para continuar.")
        return

    ok, message = consume_viability_credit(user_id=user_id)
    if ok:
        st.session_state.report_unlocked = True
        st.session_state.show_inline_payments = False
        st.success("Relatório liberado com sucesso.")
        st.session_state.scroll_to_item3 = True
    else:
        st.warning(message or "Não foi possível consumir o crédito.")
        st.session_state.show_inline_payments = True


_inject_global_styles()
_set_defaults()
handle_oauth_callback()
_render_topbar()
_render_main_title()
_ensure_sidebar_anchor()

# Top login area
render_google_login_top()

if st.session_state.get("auth_logged_in") and st.session_state.get("auth_user_id"):
    _render_wallet_block()

zones_geojson = _zones_geojson()
zones_prepared = _zones_prepared()
calc = _get_calc_context()

col1, col2 = st.columns([1.15, 1], gap="large")

with col1:
    st.markdown("## 1. Selecione o terreno")
    render_mapa_section(zones_geojson, zones_prepared)

with col2:
    st.markdown("## 2. Dados do lote")
    render_lote_section()

st.markdown('<div id="item-3-start"></div>', unsafe_allow_html=True)
st.markdown("## 3. Análise inicial")

render_localizacao_section(calc)

rule = None
if calc.get("zone_sigla") and calc.get("use_type_code"):
    try:
        rule = fetch_rule(
            zone_sigla=calc.get("zone_sigla"),
            use_type_code=calc.get("use_type_code"),
            subzone_code=calc.get("subzone_code"),
        )
    except Exception:
        rule = None

render_indices_section(
    calc=calc,
    card_func=_card,
    pick_func=pick_rule,
)

lot_area = calc.get("lot_area_m2")
built_ground = calc.get("built_ground_m2")
permeable_area = calc.get("permeable_area_m2")
can_offer_report = bool(calc)

st.markdown("---")
st.markdown("## Relatório completo")

if not st.session_state.get("auth_logged_in"):
    st.info("Entre com sua conta para liberar sua carteira e o relatório completo.")
    _render_login_gate_box()
else:
    current_balance = get_credit_balance(st.session_state.get("auth_user_id"))
    cta_label = f"📄 Gerar relatório (saldo atual: {current_balance} crédito{'s' if current_balance != 1 else ''})"
    if st.button(cta_label, type="primary", use_container_width=True):
        _offer_report_gate(can_offer_report)

if st.session_state.get("show_inline_payments"):
    st.markdown('<div id="planos"></div>', unsafe_allow_html=True)
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

        st.download_button(
            label="⬇️ Baixar relatório em PDF",
            data=pdf_bytes,
            file_name="relatorio_viabilidade.pdf",
            mime="application/pdf",
            key="download_report_pdf",
            use_container_width=True,
        )
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
