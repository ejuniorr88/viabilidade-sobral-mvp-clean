import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

import streamlit as st
import streamlit.components.v1 as components

from ui.app_shell import (
    inject_global_styles,
    render_auth_callback_bridge,
    render_login_gate_block,
    render_top_nav,
    render_wallet_summary,
)

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
from core.auth import handle_oauth_callback, safe_get_query_param
from ui.auth_panel import render_google_login_top
from ui.access_gates import (
    render_login_gate_block,
    render_client_area_gate,
    resolve_calculate_access,
    render_login_gate_if_needed,
)
from ui.payments_panel import render_payments_panel
from ui.relatorio_blocks.multifamiliar_guia import (
    render_multifamiliar_inadequado_preview,
    should_block_multifamiliar_preview,
)
from ui.client_area import render_client_area_page
from core.credits import consume_viability_credit, get_credit_balance, reconcile_wallet_to_current_user
from core.report_pdf import generate_report_pdf_bytes
from core.client_reports import save_client_report, build_report_signature
from core import report_confirmation as report_confirmation_core


@st.cache_data(show_spinner=False)
def _zones_geojson() -> Dict[str, Any]:
    with open(ZONE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_resource(show_spinner=False)
def _zones_prepared():
    return load_zones(ZONE_FILE)



def _current_report_session_snapshot(calc_ref, built_ground_value, permeable_area_value):
    return report_confirmation_core.current_report_session_snapshot(
        calc_ref=calc_ref,
        built_ground_value=built_ground_value,
        permeable_area_value=permeable_area_value,
        session_state=st.session_state,
    )


def _commit_report_snapshot(calc_ref, session_snapshot, pdf_bytes, signature):
    report_confirmation_core.commit_report_snapshot(
        session_state=st.session_state,
        calc_ref=calc_ref,
        session_snapshot=session_snapshot,
        pdf_bytes=pdf_bytes,
        signature=signature,
    )


def _clear_pending_report():
    report_confirmation_core.clear_pending_report(st.session_state)


def _clear_report_runtime_state(
    *,
    clear_last_calc_signature: bool = False,
    preserve_snapshot: bool = False,
    preserve_pending: bool = False,
) -> None:
    report_confirmation_core.clear_report_runtime_state(
        session_state=st.session_state,
        clear_last_calc_signature=clear_last_calc_signature,
        preserve_snapshot=preserve_snapshot,
        preserve_pending=preserve_pending,
    )


def _build_current_report_signature(calc_ref, session_snapshot):
    return build_report_signature(calc=calc_ref, session_state=session_snapshot)


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


if safe_get_query_param("auth_flow") == "callback":
    render_auth_callback_bridge()

handle_oauth_callback()
inject_global_styles()
render_top_nav()

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
    _clear_report_runtime_state(preserve_snapshot=True, preserve_pending=True)
    st.session_state.free_calc_done = False
    st.session_state.calc.pop("err", None)
    st.session_state.calc.pop("rule", None)

calc = st.session_state.calc
user_logged_in = bool(st.session_state.get("auth_logged_in"))
user_id = st.session_state.get("auth_user_id")
user_email = st.session_state.get("auth_user_email")
user_name = st.session_state.get("auth_user_name") or st.session_state.get("auth_name") or "—"

if st.session_state.get("post_login_action") == "open_client_area" and user_logged_in and user_id:
    st.session_state["show_client_area"] = True
    st.session_state["post_login_action"] = None

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
    _clear_report_runtime_state(preserve_snapshot=True)
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
    _clear_report_runtime_state(preserve_snapshot=True)
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

    report_confirmation_state = report_confirmation_core.compute_report_confirmation_state(
        calc_ref=calc,
        built_ground_value=built_ground,
        permeable_area_value=permeable_area,
        session_state=st.session_state,
        signature_builder=_build_current_report_signature,
    )
    current_report_session = report_confirmation_state["current_report_session"]
    current_report_signature = report_confirmation_state["current_report_signature"]
    snapshot_signature = report_confirmation_state["snapshot_signature"]
    has_snapshot = report_confirmation_state["has_snapshot"]
    is_same_as_snapshot = report_confirmation_state["is_same_as_snapshot"]

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
            _clear_report_runtime_state(preserve_snapshot=True)
            st.error("Este estudo está bloqueado por inadequabilidade. O crédito foi preservado.")
        elif not user_logged_in or not user_id:
            st.error("Faça login com Google para gerar o relatório completo.")
        elif has_snapshot and not is_same_as_snapshot:
            report_confirmation_core.arm_new_report_confirmation(
                session_state=st.session_state,
                calc_ref=deepcopy(calc),
                current_report_session=deepcopy(current_report_session),
                current_report_signature=current_report_signature,
            )
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

    if st.session_state.get("confirm_new_report") and st.session_state.get("pending_report_signature"):
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
                _clear_report_runtime_state(preserve_snapshot=True)
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
