import os
import json
import pathlib
from pathlib import Path
from typing import Any, Dict

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Viabilidade Fácil")

st.write("APP VERSION MARKER: 2026-03-11-LAYOUT-REORGANIZED-V1")
st.write("CWD:", os.getcwd())
st.write("FILES in data/:", [p.name for p in pathlib.Path("data").glob("*")])

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
from core.credits import consume_viability_credit, get_credit_balance


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


def _render_login_gate_block() -> None:
    """
    Bloco inferior de login.
    Continua aparecendo apenas quando o usuário tenta calcular sem estar logado.
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


def _render_top_nav() -> None:
    """
    Menu superior visual.
    Mantido separado da lógica de autenticação para não quebrar o fluxo já consolidado.
    """
    st.markdown(
        """
        <style>
        .vf-nav-wrap {
            background: #ffffff;
            border: 1px solid #ececec;
            border-radius: 14px;
            padding: 14px 22px;
            margin-bottom: 18px;
            box-shadow: 0 1px 6px rgba(0,0,0,0.03);
        }
        .vf-nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            flex-wrap: wrap;
        }
        .vf-brand {
            font-size: 30px;
            font-weight: 800;
            color: #1f2a44;
            letter-spacing: -0.02em;
        }
        .vf-links {
            display: flex;
            gap: 26px;
            flex-wrap: wrap;
            align-items: center;
        }
        .vf-link {
            color: #24324a;
            text-decoration: none;
            font-weight: 600;
            font-size: 15px;
        }
        .vf-link:hover {
            color: #d94b4b;
        }
        .vf-main-title {
            text-align: center;
            font-size: 42px;
            font-weight: 800;
            color: #1f2a44;
            margin-top: 6px;
            margin-bottom: 16px;
        }
        .vf-section-card {
            background: #f8f9fb;
            border: 1px solid #eceef3;
            border-radius: 14px;
            padding: 16px;
            margin-bottom: 14px;
        }
        .vf-section-title {
            font-size: 26px;
            font-weight: 800;
            color: #24324a;
            margin-bottom: 12px;
        }
        .vf-subtitle {
            font-size: 15px;
            color: #5f6b7a;
            margin-top: -6px;
            margin-bottom: 12px;
        }
        .vf-label {
            font-size: 15px;
            font-weight: 700;
            color: #24324a;
            margin-bottom: 8px;
        }
        .vf-divider {
            border-top: 1px solid #e9e9e9;
            margin: 18px 0;
        }
        .vf-badge-soon {
            display: inline-block;
            font-size: 12px;
            font-weight: 700;
            color: #b85b00;
            background: #fff4e8;
            border: 1px solid #ffd3a8;
            border-radius: 999px;
            padding: 3px 9px;
            margin-left: 8px;
        }
        </style>

        <div class="vf-nav-wrap">
          <div class="vf-nav">
            <div class="vf-brand">Viabilidade Fácil</div>
            <div class="vf-links">
              <a class="vf-link" href="#">Como funciona</a>
              <a class="vf-link" href="#">Área do cliente</a>
              <a class="vf-link" href="#">Planos</a>
              <a class="vf-link" href="#">Dúvidas/Suporte</a>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# Session state base
# =========================================================
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


handle_oauth_callback()

zones_gj = _zones_geojson()
zones_prepared = _zones_prepared()

# =========================================================
# Topo
# =========================================================
_render_top_nav()

top_left, top_right = st.columns([2, 1])
with top_left:
    st.markdown('<div class="vf-main-title">Viabilidade Urbana</div>', unsafe_allow_html=True)
with top_right:
    render_google_login_top()
    render_credits_panel(_card)

# =========================================================
# Layout principal: sidebar visual + conteúdo
# =========================================================
sidebar_col, main_col = st.columns([1.05, 3.25], gap="large")

with sidebar_col:
    st.markdown("### 1. Escolha o Uso")

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
        "Residencial Unifamiliar (Casa)": "RES_UNI",
        "Multifamiliar R2.1 (2 unidades no mesmo lote)": "RES_MULTI_R21",
        "Multifamiliar R2.2 (condomínio horizontal com via interna)": "RES_MULTI_R22",
        "Multifamiliar R3 (condomínio vertical / prédio)": "RES_MULTI_R3",
    }

    selected_use_label = st.selectbox(
        "Opções na Categoria:",
        options=list(residential_options.keys()),
        index=0,
        key="vf_residential_option",
        disabled=(categoria_label != "Residencial"),
    )

    st.session_state.calc["use_type_code"] = residential_options.get(selected_use_label, "RES_UNI")

    if categoria_label != "Residencial":
        st.caption("Essa categoria ficará disponível em breve.")
    st.markdown("---")

    st.markdown("### 2. Busca Direta")
    st.text_input(
        "Ou digite para pesquisar:",
        value="Em breve",
        disabled=True,
        key="vf_busca_direta",
    )
    st.caption("A busca direta ficará disponível em breve.")
    st.markdown("---")

    st.markdown("### 3. Dados do Lote")
    st.caption(
        "Mantido o bloco funcional já consolidado, incluindo a lógica de terreno irregular."
    )

    # Comentário importante:
    # render_lote_section continua sendo usado para preservar a lógica consolidada
    # de dados do lote, inclusive terreno irregular.
    lot_area, built_ground, permeable_area = render_lote_section()

with main_col:
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
            # Comentário importante:
            # limpeza controlada do estado, preservando a estrutura base.
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

# =========================================================
# Dados base do lote
# =========================================================
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

# Se mudou algum dado do estudo, invalida cálculo gratuito e relatório pago
if st.session_state.last_calc_signature and st.session_state.last_calc_signature != current_signature:
    st.session_state.report_unlocked = False
    st.session_state.free_calc_done = False
    st.session_state.show_inline_payments = False
    st.session_state.calc.pop("err", None)
    st.session_state.calc.pop("rule", None)

calc = st.session_state.calc
user_logged_in = bool(st.session_state.get("auth_logged_in"))
user_id = st.session_state.get("auth_user_id")

# =========================================================
# Âncora do login inferior
# =========================================================
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

# Continuação automática após login
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

# Bloco inferior de login
if st.session_state.get("show_login_gate") and not (user_logged_in and user_id):
    _render_login_gate_block()
    st.divider()

# =========================================================
# Âncora do item 3
# O item 3 só aparece depois do cálculo
# =========================================================
st.markdown('<div id="item-3-start"></div>', unsafe_allow_html=True)

show_item3 = bool(run_free_calc_now or st.session_state.get("free_calc_done"))

# =========================================================
# Cálculo gratuito (somente logado)
# =========================================================
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

# =========================================================
# Parte gratuita: mostrar apenas depois do cálculo
# =========================================================
if st.session_state.get("free_calc_done"):
    render_indices_section(
        calc=calc,
        card_func=_card,
        pick_func=pick_rule,
        get_rule_func=fetch_rule,
    )

# =========================================================
# Botão para gerar relatório (parte paga)
# =========================================================
can_offer_report = bool(st.session_state.get("free_calc_done")) and bool(calc.get("zone")) and not bool(calc.get("err"))

if can_offer_report:
    st.markdown("---")
    st.subheader("Relatório completo")
    st.caption(
        "A análise inicial acima é gratuita. Para liberar o relatório completo, "
        "gere o relatório com 1 crédito."
    )

    user_logged_in = bool(st.session_state.get("auth_logged_in"))
    user_id = st.session_state.get("auth_user_id")

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
        else:
            try:
                debit_result = consume_viability_credit(
                    user_id=user_id,
                    amount=1,
                    description="Geração de relatório de viabilidade",
                )

                if not debit_result.get("ok"):
                    st.session_state.show_inline_payments = True
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
                st.error(f"Não foi possível descontar o crédito: {e}")

    # Planos inline logo abaixo do botão de relatório
    if st.session_state.get("show_inline_payments"):
        st.markdown("### Comprar créditos")
        render_payments_panel()

# =========================================================
# Parte paga: item 5 + relatório final
# =========================================================
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

# =========================================================
# Scroll isolado para o login inferior
# =========================================================
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

# =========================================================
# Scroll isolado para o começo do item 3
# =========================================================
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
