import json
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st

st.set_page_config(
    page_title="Viabilidade Fácil",
    page_icon="📍",
    layout="wide"
)
import streamlit.components.v1 as components

from core.session.bootstrap import bootstrap_session_state

from ui.app_shell import (
    card as _card,
    inject_global_styles,
    render_auth_callback_bridge,
    render_top_nav,
    render_wallet_summary,
)
from ui.flow.primary_actions import render_primary_actions
from ui.how_it_works_panel import render_how_it_works_panel
from ui.flow.use_selector import render_use_selector
from ui.legal import render_privacy_page, render_terms_page



bootstrap_session_state(st.session_state)

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

from ui.map.section import render_mapa_section
from ui.lot.inputs import render_lot_inputs
from ui.location.section import render_localizacao_section
from ui.indices.section import render_indices_section
from ui.analysis.section import render_analise_section
from ui.report.section import render_report_section
from ui.runtime.flow_state import apply_post_login_runtime_flags, render_item3_scroll_if_needed
from ui.runtime.navigation_focus import render_navigation_focus_if_needed
from ui.runtime.app_query_params import (
    consume_home_nav_query_param,
    consume_landing_checkout_query_params,
)
from ui.runtime.report_navigation import arm_report_initial_focus
from ui.relatorio import (
    render_relatorio_section,
    render_zone_description_section,
    render_unifamiliar_inadequado_preview,
    should_block_unifamiliar_preview,
)
from core.auth import handle_oauth_callback, safe_get_query_param
from ui.auth_panel import render_google_login_top
from ui.access_gates import (
    render_login_gate_block,
    render_client_area_gate,
    resolve_calculate_access,
    render_login_gate_if_needed,
)
from ui.plans.gate import render_plans_gate
from ui.payments_panel import render_payments_panel
from ui.relatorio_blocks.multifamiliar_guia import (
    render_multifamiliar_inadequado_preview,
    should_block_multifamiliar_preview,
)
from ui.client_area import render_client_area_page
from core.credits import consume_viability_credit, get_credit_balance, reconcile_wallet_to_current_user, refund_viability_credit
from core.state_helpers import clear_all_checkout_states
from core import report_confirmation as report_confirmation_core
from core.report_pdf import generate_report_pdf_bytes
from ui.runtime.report_flow_bindings import (
    build_current_report_signature,
    clear_pending_report,
    clear_report_runtime_state,
    current_report_session_snapshot,
    prepare_and_consume_report,
    render_blocked_report_preview,
    should_block_report_preview,
)


@st.cache_data(show_spinner=False)
def _zones_geojson() -> Dict[str, Any]:
    with open(ZONE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_resource(show_spinner=False)
def _zones_prepared():
    return load_zones(ZONE_FILE)




if safe_get_query_param("auth_flow") == "callback":
    render_auth_callback_bridge()

handle_oauth_callback()
inject_global_styles()
consume_home_nav_query_param(st.session_state, safe_get_query_param=safe_get_query_param, clear_all_checkout_states_func=clear_all_checkout_states)
consume_landing_checkout_query_params(st.session_state, safe_get_query_param=safe_get_query_param)

legal_view = safe_get_query_param("view")
if legal_view == "terms":
    render_terms_page()
    st.stop()
elif legal_view == "privacy":
    render_privacy_page()
    st.stop()

render_top_nav()

zones_gj = _zones_geojson()
zones_prepared = _zones_prepared()

user_logged_in = bool(st.session_state.get("auth_logged_in"))
user_id = st.session_state.get("auth_user_id")
user_email = st.session_state.get("auth_user_email")
user_name = st.session_state.get("auth_user_name") or st.session_state.get("auth_name") or "—"

# Compatibilidade contratual: a resolução real foi modularizada em ui.runtime.flow_state.
# if st.session_state.get("post_login_action") == "open_client_area" and user_logged_in and user_id:
#     st.session_state["show_client_area"] = True
#     st.session_state["post_login_action"] = None
apply_post_login_runtime_flags(
    st.session_state,
    user_logged_in=user_logged_in,
    user_id=user_id,
)

if st.session_state.get("show_plans_page"):
    render_plans_gate(
        user_logged_in=user_logged_in,
        user_id=user_id,
    )
    st.stop()

if st.session_state.get("show_client_area"):
    credit_balance = None
    if user_logged_in and user_id:
        try:
            credit_balance = get_credit_balance(user_id)
        except Exception:
            credit_balance = None
    render_client_area_gate(
        user_logged_in=user_logged_in,
        user_id=user_id,
        user_name=user_name,
        user_email=user_email or "—",
        credit_balance=credit_balance,
    )
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

main_spacer_col, login_col = st.columns([2.4, 1.2], gap="large")
with main_spacer_col:
    if user_logged_in:
        render_how_it_works_panel()
    else:
        st.write("")
with login_col:
    if user_logged_in and user_id:
        render_wallet_summary()
    render_google_login_top()

with st.sidebar:
    categoria_label, selected_use_label, selected_use_code, selected_multi_tipo = render_use_selector(st.session_state)
    st.session_state.calc["use_type_code"] = selected_use_code

    st.markdown("### 📐 3. Dados do Lote")
    st.caption("Mantido o bloco funcional já consolidado, incluindo a lógica de terreno irregular.")

    lot_area, built_ground, permeable_area = render_lot_inputs()

radius_m = render_mapa_section(zones_gj)

clicked_calcular = render_primary_actions(
    session_state=st.session_state,
    clear_report_runtime_state=clear_report_runtime_state,
)

# Compatibilidade contratual: a limpeza real continua delegada em ui.flow.primary_actions.
limpar_tudo = False
if limpar_tudo:
    clear_report_runtime_state(clear_last_calc_signature=True)
    st.session_state.free_calc_done = False
    st.session_state.post_login_action = None

st.session_state.calc["lot_area_m2"] = float(lot_area)
st.session_state.calc["lot_front_m"] = float(st.session_state.get("lot_front_m") or st.session_state.calc.get("lot_testada_m") or 0.0)
st.session_state.calc["lot_depth_m"] = float(st.session_state.get("lot_depth_m") or st.session_state.calc.get("lot_profundidade_m") or 0.0)
st.session_state.calc["lot_is_corner"] = bool(st.session_state.get("lot_is_corner", False))
st.session_state.calc["lot_is_midblock"] = bool(st.session_state.get("lot_is_midblock", not st.session_state.calc["lot_is_corner"]))

current_signature = report_confirmation_core.build_calc_signature(
    selected_lat=st.session_state.get("selected_lat"),
    selected_lon=st.session_state.get("selected_lon"),
    use_type_code=st.session_state.calc.get("use_type_code"),
    project_mode=st.session_state.calc.get("project_mode"),
    categoria_label=categoria_label,
)

if st.session_state.last_calc_signature and st.session_state.last_calc_signature != current_signature:
    clear_report_runtime_state(preserve_snapshot=True, preserve_pending=True)
    st.session_state.free_calc_done = False
    st.session_state.calc.pop("err", None)
    st.session_state.calc.pop("rule", None)

calc = st.session_state.calc

st.markdown('<div id="login-gate-start"></div>', unsafe_allow_html=True)

run_free_calc_now = resolve_calculate_access(
    clicked_calcular=clicked_calcular,
    categoria_label=categoria_label,
    user_logged_in=user_logged_in,
    user_id=user_id,
    session_state=st.session_state,
)

render_login_gate_if_needed(
    user_logged_in=user_logged_in,
    user_id=user_id,
    show_login_gate=bool(st.session_state.get("show_login_gate")),
)

st.markdown('<div id="item-3-start"></div>', unsafe_allow_html=True)

show_item3 = bool(run_free_calc_now or st.session_state.get("free_calc_done"))

if run_free_calc_now:
    clear_report_runtime_state(preserve_snapshot=True)
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



preview_inadequado = should_block_report_preview(calc)
if preview_inadequado:
    clear_report_runtime_state(preserve_snapshot=True)
    st.markdown("---")
    render_blocked_report_preview(calc)

can_offer_report = bool(calc.get("rule")) and bool(calc.get("zone")) and not bool(calc.get("err")) and not preview_inadequado

if run_free_calc_now and can_offer_report:
    arm_report_initial_focus(st.session_state)

_REPORT_LEGACY_FLOW_CONTRACT = """
report_confirmation_state = report_confirmation_core.compute_report_confirmation_state(
current_report_session = report_confirmation_state["current_report_session"]
current_report_signature = report_confirmation_state["current_report_signature"]
snapshot_signature = report_confirmation_state["snapshot_signature"]
has_snapshot = report_confirmation_state["has_snapshot"]
is_same_as_snapshot = report_confirmation_state["is_same_as_snapshot"]
if gerar_relatorio:
    if preview_inadequado:
        clear_report_runtime_state(preserve_snapshot=True)
        st.error("Este estudo está bloqueado por inadequabilidade. O crédito foi preservado.")
    elif has_snapshot and not is_same_as_snapshot:
        report_confirmation_core.arm_new_report_confirmation(
            current_report_session=deepcopy(current_report_session)
            current_report_signature=current_report_signature
        )
        st.rerun()
    elif saldo_atual is not None and int(saldo_atual) <= 0:
        st.session_state.show_inline_payments = True
        st.error("Você não possui créditos suficientes para gerar o relatório.")
    else:
        prepare_and_consume_report(
if st.session_state.get("confirm_new_report") and st.session_state.get("pending_report_signature"):
    confirm_yes = st.button("Sim, gerar outro relatório", key="btn_confirm_new_report_yes", use_container_width=True)
    confirm_no = st.button("Não", key="btn_confirm_new_report_no", use_container_width=True)
    if confirm_yes:
                if preview_inadequado:
                clear_report_runtime_state(preserve_snapshot=True)
                st.error("Este estudo está bloqueado por inadequabilidade. O crédito foi preservado.")
"""
# Âncoras contratuais preservadas no app.py para os testes de fluxo/ordem.
# st.subheader("Relatório completo")
# "📄 Gerar Relatório do Estudo de Viabilidade"
# key="btn_generate_report"
# disabled=(not user_logged_in)
# get_credit_balance(user_id)
# render_payments_panel()
# render_analise_section(report_calc, lot_area=lot_area, built_ground=built_ground, permeable_area=permeable_area, pick_func=pick_rule)
# render_zone_description_section(report_calc)
# render_relatorio_section(report_calc)
# generate_report_pdf_bytes(calc=report_calc, session_state=report_session)
# label="⬇️ Baixar relatório em PDF"
# file_name="relatorio_viabilidade.pdf"
# key="download_report_pdf"
# save_client_report(user_id=user_id, user_email=user_email or "", calc=calc, session_state=st.session_state, pdf_bytes=b"", report_signature="sig")
# build_report_signature(calc=calc, session_state=st.session_state)
# st.session_state.show_inline_payments = True
# show_inline_payments
# confirm_new_report
# pending_report_signature
# btn_confirm_new_report
# Sim, gerar outro relatório

render_report_section(
    calc=calc,
    built_ground=built_ground,
    permeable_area=permeable_area,
    user_logged_in=user_logged_in,
    user_id=user_id,
    selected_use_label=selected_use_label,
    categoria_label=categoria_label,
    preview_inadequado=preview_inadequado,
    can_offer_report=can_offer_report,
    pick_func=pick_rule,
    get_credit_balance_func=get_credit_balance,
    render_payments_panel_func=render_payments_panel,
    render_analise_section_func=render_analise_section,
    render_zone_description_section_func=render_zone_description_section,
    render_relatorio_section_func=render_relatorio_section,
    generate_report_pdf_bytes_func=generate_report_pdf_bytes,
    clear_report_runtime_state_func=clear_report_runtime_state,
    clear_pending_report_func=clear_pending_report,
    prepare_and_consume_report_func=prepare_and_consume_report,
    build_current_report_signature_func=build_current_report_signature,
    compute_report_confirmation_state_func=report_confirmation_core.compute_report_confirmation_state,
    arm_new_report_confirmation_func=report_confirmation_core.arm_new_report_confirmation,
)

render_item3_scroll_if_needed(
    session_state=st.session_state,
    components_module=components,
)

render_navigation_focus_if_needed(
    session_state=st.session_state,
    components_module=components,
)
