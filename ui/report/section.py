from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Dict

import streamlit as st
import streamlit.components.v1 as components

from ui.report.final_confirmation import render_final_confirmation
from ui.report.review_panel import render_review_panel
from ui.report.terms_gate import render_terms_gate
from ui.runtime.inline_payments_focus import arm_inline_payments_focus
from ui.runtime.report_navigation import (
    arm_report_confirmation_focus,
    arm_report_generated_focus,
    arm_report_initial_focus,
)

_REVIEW_OPEN_KEY = "report_review_open"
_REVIEW_SIGNATURE_KEY = "report_review_signature"
_REVIEW_CALC_KEY = "report_review_calc"
_REVIEW_SESSION_KEY = "report_review_session"
_REVIEW_IS_NEW_KEY = "report_review_is_new_report"
_NOTICE_FOCUS_SIGNATURE_KEY = "report_section_notice_focus_signature"
_LEGACY_GENERATE_REPORT_LABEL = "📄 Gerar relatório"


def _render_generate_report_button_style() -> None:
    """Aplica um destaque visual discreto no botão inicial do relatório.

    Usa script leve no DOM para evitar depender de seletores frágeis do Streamlit
    que podem deixar o botão branco ou perder o estilo entre reruns.
    """

    components.html(
        """
        <script>
        const styleButton = () => {
            const rootDoc = window.parent.document;
            const buttons = [...rootDoc.querySelectorAll('div[data-testid="stButton"] button')];
            const target = buttons.find((btn) =>
                (btn.innerText || '').trim().includes('Gerar Relatório do Estudo de Viabilidade')
            );
            if (!target) return false;

            target.style.background = 'linear-gradient(180deg, #eef4ff 0%, #e7f0ff 100%)';
            target.style.border = '1px solid #c7d5ea';
            target.style.color = '#173b69';
            target.style.fontWeight = '700';
            target.style.boxShadow = '0 2px 10px rgba(23, 59, 105, 0.08)';
            target.style.transition = 'all 0.15s ease';

            target.onmouseenter = () => {
                target.style.background = 'linear-gradient(180deg, #f3f7ff 0%, #eaf2ff 100%)';
                target.style.borderColor = '#9db6d8';
                target.style.color = '#122f56';
            };
            target.onmouseleave = () => {
                target.style.background = 'linear-gradient(180deg, #eef4ff 0%, #e7f0ff 100%)';
                target.style.borderColor = '#c7d5ea';
                target.style.color = '#173b69';
            };
            return true;
        };

        if (!styleButton()) {
            setTimeout(styleButton, 120);
            setTimeout(styleButton, 350);
        }
        </script>
        """,
        height=0,
    )




def _build_notice_focus_signature(*, report_signature: str | None, session_snapshot: Dict[str, Any], built_ground: Any, permeable_area: Any) -> str:
    lot_front = session_snapshot.get("lot_front_m")
    lot_depth = session_snapshot.get("lot_depth_m")
    lot_area = session_snapshot.get("lot_area_m2")
    return "|".join(
        [
            str(report_signature or ""),
            str(lot_front if lot_front is not None else ""),
            str(lot_depth if lot_depth is not None else ""),
            str(lot_area if lot_area is not None else ""),
            str(built_ground if built_ground is not None else ""),
            str(permeable_area if permeable_area is not None else ""),
        ]
    )

def _clear_review_state() -> None:
    st.session_state[_REVIEW_OPEN_KEY] = False
    st.session_state[_REVIEW_SIGNATURE_KEY] = None
    st.session_state[_REVIEW_CALC_KEY] = None
    st.session_state[_REVIEW_SESSION_KEY] = None
    st.session_state[_REVIEW_IS_NEW_KEY] = False


def _arm_review_state(*, calc: Dict[str, Any], session_snapshot: Dict[str, Any], signature: str, is_new_report: bool) -> None:
    st.session_state[_REVIEW_OPEN_KEY] = True
    st.session_state[_REVIEW_SIGNATURE_KEY] = signature
    st.session_state[_REVIEW_CALC_KEY] = deepcopy(calc)
    st.session_state[_REVIEW_SESSION_KEY] = deepcopy(session_snapshot)
    st.session_state[_REVIEW_IS_NEW_KEY] = bool(is_new_report)


def render_report_section(
    *,
    calc: Dict[str, Any],
    built_ground: Any,
    permeable_area: Any,
    user_logged_in: bool,
    user_id: str | None,
    selected_use_label: str,
    categoria_label: str,
    preview_inadequado: bool,
    can_offer_report: bool,
    pick_func: Callable[..., Any],
    get_credit_balance_func: Callable[[str], Any],
    render_payments_panel_func: Callable[[], None],
    render_analise_section_func: Callable[..., None],
    render_zone_description_section_func: Callable[[Dict[str, Any]], None],
    render_relatorio_section_func: Callable[[Dict[str, Any]], None],
    generate_report_pdf_bytes_func: Callable[..., bytes],
    clear_report_runtime_state_func: Callable[..., None],
    clear_pending_report_func: Callable[[], None],
    prepare_and_consume_report_func: Callable[..., Any],
    build_current_report_signature_func: Callable[..., Any],
    compute_report_confirmation_state_func: Callable[..., Dict[str, Any]],
    arm_new_report_confirmation_func: Callable[..., Any],
) -> None:
    if can_offer_report:
        st.markdown('<div id="report-section-start"></div>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown('<div id="report-generated-context-start"></div>', unsafe_allow_html=True)
        st.subheader("Relatório completo")
        st.caption(
            "A análise inicial acima é gratuita. Para liberar o relatório completo, "
            "gere o relatório com 1 crédito."
        )

        report_confirmation_state = compute_report_confirmation_state_func(
            calc_ref=calc,
            built_ground_value=built_ground,
            permeable_area_value=permeable_area,
            session_state=st.session_state,
            signature_builder=build_current_report_signature_func,
        )
        current_report_session = report_confirmation_state["current_report_session"]
        current_report_signature = report_confirmation_state["current_report_signature"]
        has_snapshot = report_confirmation_state["has_snapshot"]
        is_same_as_snapshot = report_confirmation_state["is_same_as_snapshot"]

        review_signature_changed = bool(
            st.session_state.get(_REVIEW_OPEN_KEY)
            and st.session_state.get(_REVIEW_SIGNATURE_KEY)
            and st.session_state.get(_REVIEW_SIGNATURE_KEY) != current_report_signature
        )
        pending_signature_changed = bool(
            st.session_state.get("pending_report_signature")
            and st.session_state.get("pending_report_signature") != current_report_signature
        )

        if review_signature_changed:
            clear_pending_report_func()
            _arm_review_state(
                calc=calc,
                session_snapshot=current_report_session,
                signature=current_report_signature,
                is_new_report=bool(has_snapshot and not is_same_as_snapshot),
            )
            arm_report_confirmation_focus(st.session_state)
        elif pending_signature_changed:
            clear_pending_report_func()

        saldo_atual = None
        if user_logged_in and user_id:
            try:
                saldo_atual = get_credit_balance_func(user_id)
            except Exception:
                saldo_atual = None

        c1, c2 = st.columns([1, 2])
        with c1:
            gerar_relatorio = st.button(
                "📄 Gerar Relatório do Estudo de Viabilidade",
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

        _render_generate_report_button_style()

        if gerar_relatorio:
            if preview_inadequado:
                clear_report_runtime_state_func(preserve_snapshot=True)
                st.error("Este estudo está bloqueado por inadequabilidade. O crédito foi preservado.")
            elif not user_logged_in or not user_id:
                st.error("Faça login com Google para gerar o relatório completo.")
            elif is_same_as_snapshot:
                arm_report_initial_focus(st.session_state)
                st.info("Este relatório já foi gerado e continua disponível abaixo.")
            elif saldo_atual is not None and int(saldo_atual) <= 0:
                st.session_state.show_inline_payments = True
                arm_inline_payments_focus(st.session_state)
                st.error("Você não possui créditos suficientes para gerar o relatório.")
            else:
                # Mantém compatibilidade com o contrato legado do runtime e dos testes
                # que esperam a chamada explícita desta âncora antes da abertura do
                # novo fluxo de revisão modularizado.
                arm_new_report_confirmation_func(
                    session_state=st.session_state,
                    calc_ref=calc,
                    current_report_session=current_report_session,
                    current_report_signature=current_report_signature,
                )
                _arm_review_state(
                    calc=calc,
                    session_snapshot=current_report_session,
                    signature=current_report_signature,
                    is_new_report=bool(has_snapshot and not is_same_as_snapshot),
                )
                arm_report_confirmation_focus(st.session_state)
                st.rerun()

        if st.session_state.get(_REVIEW_OPEN_KEY):
            st.markdown('<div id="report-review-start"></div>', unsafe_allow_html=True)
            review_calc = deepcopy(st.session_state.get(_REVIEW_CALC_KEY) or calc)
            review_session = deepcopy(st.session_state.get(_REVIEW_SESSION_KEY) or current_report_session)
            review_sig = st.session_state.get(_REVIEW_SIGNATURE_KEY) or current_report_signature
            is_new_report = bool(st.session_state.get(_REVIEW_IS_NEW_KEY))

            render_review_panel(calc=review_calc, session_snapshot=review_session)
            accepted = render_terms_gate(signature=review_sig)
            st.markdown('<div id="report-review-confirm-start"></div>', unsafe_allow_html=True)
            confirm_yes, confirm_no = render_final_confirmation(is_new_report=is_new_report)

            if confirm_no:
                _clear_review_state()
                arm_report_initial_focus(st.session_state)
                st.rerun()

            if confirm_yes:
                if not accepted:
                    st.error("Para seguir, você precisa aceitar os Termos de Uso e a Política de Privacidade.")
                elif preview_inadequado:
                    _clear_review_state()
                    clear_report_runtime_state_func(preserve_snapshot=True)
                    st.error("Este estudo está bloqueado por inadequabilidade. O crédito foi preservado.")
                else:
                    try:
                        debit_result, _ = prepare_and_consume_report_func(
                            calc_ref=deepcopy(review_calc),
                            session_snapshot=deepcopy(review_session),
                            report_signature=review_sig,
                            user_id_value=user_id,
                            selected_use_label_value=selected_use_label,
                            categoria_label_value=categoria_label,
                        )
                        novo_saldo = debit_result.get("new_balance")
                        _clear_review_state()
                        clear_pending_report_func()
                        st.success(f"1 crédito consumido com sucesso. Saldo atual: {novo_saldo}")
                        arm_report_initial_focus(st.session_state)
                        st.rerun()
                    except Exception as e:
                        st.session_state.show_inline_payments = True
                        arm_inline_payments_focus(st.session_state)
                        st.error(f"Não foi possível preparar e gerar o relatório: {e}")

            return

        is_review_open = bool(st.session_state.get(_REVIEW_OPEN_KEY))
        is_legacy_confirming = bool(
            st.session_state.get("confirm_new_report") and st.session_state.get("pending_report_signature")
        )
        notice_should_focus = bool(
            has_snapshot
            and not is_same_as_snapshot
            and not is_review_open
            and not is_legacy_confirming
        )

        if has_snapshot and not is_same_as_snapshot:
            st.markdown('<div id="report-section-scenario-notice"></div>', unsafe_allow_html=True)
            st.warning(
                "Você está visualizando um relatório já gerado. Para gerar outro relatório neste novo cenário, clique novamente em gerar relatório."
            )

            notice_focus_signature = _build_notice_focus_signature(
                report_signature=current_report_signature,
                session_snapshot=current_report_session,
                built_ground=built_ground,
                permeable_area=permeable_area,
            )
            if notice_should_focus and st.session_state.get(_NOTICE_FOCUS_SIGNATURE_KEY) != notice_focus_signature:
                arm_report_generated_focus(st.session_state)
                # Registra a última assinatura pedida para evitar re-scroll em reruns estáveis,
                # mas mantém o disparo de JS forte no runtime para o browser real.
                st.session_state[_NOTICE_FOCUS_SIGNATURE_KEY] = notice_focus_signature
        else:
            if st.session_state.get(_NOTICE_FOCUS_SIGNATURE_KEY) is not None:
                st.session_state[_NOTICE_FOCUS_SIGNATURE_KEY] = None

        # Compatibilidade com fluxo legado/testes antigos.
        if st.session_state.get("confirm_new_report") and st.session_state.get("pending_report_signature"):
            st.warning("Você tem certeza que deseja gerar outro relatório? Isso vai gastar outro crédito.")
            c_yes, c_no = st.columns(2)
            with c_yes:
                confirm_yes = st.button("Sim, gerar outro relatório", key="btn_confirm_new_report_yes", use_container_width=True)
            with c_no:
                confirm_no = st.button("Não", key="btn_confirm_new_report_no", use_container_width=True)

            if confirm_no:
                clear_pending_report_func()
                arm_report_initial_focus(st.session_state)
                st.rerun()

            if confirm_yes:
                if preview_inadequado:
                    clear_report_runtime_state_func(preserve_snapshot=True)
                    st.error("Este estudo está bloqueado por inadequabilidade. O crédito foi preservado.")
                else:
                    try:
                        pending_calc = deepcopy(st.session_state.get("pending_report_calc") or calc)
                        pending_session = deepcopy(st.session_state.get("pending_report_session") or current_report_session)
                        pending_sig = st.session_state.get("pending_report_signature") or current_report_signature
                        debit_result, _ = prepare_and_consume_report_func(
                            calc_ref=pending_calc,
                            session_snapshot=pending_session,
                            report_signature=pending_sig,
                            user_id_value=user_id,
                            selected_use_label_value=selected_use_label,
                            categoria_label_value=categoria_label,
                        )
                        novo_saldo = debit_result.get("new_balance")
                        st.success(f"1 crédito consumido com sucesso. Saldo atual: {novo_saldo}")
                        clear_pending_report_func()
                        arm_report_initial_focus(st.session_state)
                        st.rerun()
                    except Exception as e:
                        st.session_state.show_inline_payments = True
                        arm_inline_payments_focus(st.session_state)
                        st.error(f"Não foi possível preparar e gerar o novo relatório: {e}")

        if st.session_state.get("show_inline_payments"):
            st.markdown('<div id="inline-payments-start"></div>', unsafe_allow_html=True)
            st.markdown("### Comprar créditos")
            render_payments_panel_func()

    if (st.session_state.get("report_snapshot_calc") and st.session_state.get("report_snapshot_signature")) and can_offer_report:
        st.markdown("---")
        report_calc = deepcopy(st.session_state.get("report_snapshot_calc"))
        report_session = deepcopy(st.session_state.get("report_snapshot_session") or {})

        render_analise_section_func(
            report_calc,
            lot_area=report_session.get("lot_area_m2", calc.get("lot_area_m2")),
            built_ground=report_session.get("built_ground_m2", built_ground),
            permeable_area=report_session.get("permeable_area_m2", permeable_area),
            pick_func=pick_func,
        )

        render_zone_description_section_func(report_calc)
        render_relatorio_section_func(report_calc)

        st.markdown("### Download do relatório")
        try:
            pdf_bytes = st.session_state.get("last_generated_pdf_bytes")
            if not pdf_bytes or st.session_state.get("last_generated_pdf_signature") != st.session_state.get("report_snapshot_signature"):
                pdf_bytes = generate_report_pdf_bytes_func(calc=report_calc, session_state=report_session)
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
