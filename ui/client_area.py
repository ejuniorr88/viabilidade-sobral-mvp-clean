from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict
from zoneinfo import ZoneInfo

import streamlit as st

from core.client_reports import build_download_signed_url, list_client_reports
from core.coupons import user_can_manage_coupons
from ui.coupons_admin import render_coupons_admin_section
from ui.relatorio import render_relatorio_section
from core.state_helpers import clear_all_checkout_states

_TZ = ZoneInfo("America/Fortaleza")


def _to_local_label(item: Dict[str, Any]) -> tuple[str, str]:
    ctx = item.get("report_context") or {}
    saved_local = ctx.get("saved_at_local")
    if saved_local:
        try:
            dt = datetime.fromisoformat(str(saved_local))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=_TZ)
            else:
                dt = dt.astimezone(_TZ)
            return dt.strftime("%d/%m/%Y"), dt.strftime("%H:%M")
        except Exception:
            pass

    created_at = item.get("created_at")
    if created_at:
        try:
            raw = str(created_at).replace("Z", "+00:00")
            dt = datetime.fromisoformat(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=_TZ)
            dt = dt.astimezone(_TZ)
            return dt.strftime("%d/%m/%Y"), dt.strftime("%H:%M")
        except Exception:
            pass

    return "—", "—"


def _info_card(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div style="border:1px solid #e8e8e8;border-radius:14px;padding:14px 16px;background:#fff;">
          <div style="font-size:12px;color:#6b7280;margin-bottom:6px;">{label}</div>
          <div style="font-size:16px;font-weight:700;color:#1f2a44;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


_PREVIEW_REPORT_KEY = "client_area_preview_report_id"
_PREVIEW_BACKUP_SENTINEL = object()


def _apply_saved_session_snapshot(session_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    backup: Dict[str, Any] = {}
    for key, value in (session_snapshot or {}).items():
        backup[key] = st.session_state.get(key, _PREVIEW_BACKUP_SENTINEL)
        st.session_state[key] = deepcopy(value)
    return backup


def _restore_saved_session_snapshot(backup: Dict[str, Any]) -> None:
    for key, value in (backup or {}).items():
        if value is _PREVIEW_BACKUP_SENTINEL:
            try:
                del st.session_state[key]
            except Exception:
                pass
        else:
            st.session_state[key] = value


def _render_saved_report_preview(item: Dict[str, Any]) -> None:
    ctx = item.get("report_context") or {}
    calc_snapshot = ctx.get("calc_snapshot") or {}
    session_snapshot = ctx.get("session_snapshot") or {}
    if not isinstance(calc_snapshot, dict) or not calc_snapshot:
        st.info("Este relatório salvo ainda não possui snapshot visual disponível.")
        return

    st.markdown("### Visualização salva do relatório")
    st.caption("Esta visualização usa o snapshot salvo no momento da geração para reproduzir o relatório dentro da Área do Cliente.")

    backup = _apply_saved_session_snapshot(session_snapshot if isinstance(session_snapshot, dict) else {})
    try:
        render_relatorio_section(deepcopy(calc_snapshot))
    finally:
        _restore_saved_session_snapshot(backup)



def _render_reports_tab(user_id: str) -> None:
    st.markdown("### Relatórios salvos")
    try:
        reports = list_client_reports(user_id)
    except Exception as exc:
        st.warning(f"Não foi possível carregar os relatórios salvos: {exc}")
        return

    if not reports:
        st.info("Você ainda não possui relatórios salvos na sua área do cliente.")
        return

    for item in reports:
        date_label, time_label = _to_local_label(item)
        title = item.get("title") or "Relatório salvo"
        zone = item.get("zone_label") or "—"
        road = item.get("road_name") or "—"
        path = item.get("pdf_storage_path") or ""

        st.markdown(
            f"""
            <div style="border:1px solid #e8e8e8;border-radius:16px;padding:16px 18px;background:#fff;margin-bottom:14px;">
              <div style="font-size:18px;font-weight:800;color:#1f2a44;margin-bottom:10px;">{title}</div>
              <div style="font-size:14px;color:#4b5563;margin-bottom:8px;">Zona: <b>{zone}</b> &nbsp; • &nbsp; Rua: <b>{road}</b></div>
              <div style="font-size:14px;color:#4b5563;">Data: <b>{date_label}</b> &nbsp; • &nbsp; Horário: <b>{time_label}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        a, b, c, d, e = st.columns([1.1, 1.3, 1.0, 1.5, 2.5])
        with a:
            st.text_input("Zona", value=zone, disabled=True, key=f"zone_{item.get('id')}")
        with b:
            st.text_input("Rua", value=road, disabled=True, key=f"road_{item.get('id')}")
        with c:
            st.text_input("Horário", value=time_label, disabled=True, key=f"time_{item.get('id')}")
        with d:
            is_open = st.session_state.get(_PREVIEW_REPORT_KEY) == item.get("id")
            if is_open:
                if st.button("Fechar visualização", use_container_width=True, key=f"preview_close_{item.get('id')}"):
                    st.session_state[_PREVIEW_REPORT_KEY] = None
            else:
                if st.button("👁️ Visualizar", use_container_width=True, key=f"preview_open_{item.get('id')}"):
                    st.session_state[_PREVIEW_REPORT_KEY] = item.get("id")
        with e:
            signed_url = ""
            try:
                signed_url = build_download_signed_url(path)
            except Exception:
                signed_url = ""
            if signed_url:
                st.link_button("⬇️ Fazer download", signed_url, use_container_width=True)
            else:
                st.button("⬇️ Fazer download", disabled=True, use_container_width=True, key=f"download_disabled_{item.get('id')}")

        if st.session_state.get(_PREVIEW_REPORT_KEY) == item.get("id"):
            _render_saved_report_preview(item)




def _client_area_tabs_for_user(user_email: str) -> list[str]:
    tabs = ["Relatórios"]
    if user_can_manage_coupons(user_email):
        tabs.append("Cupons")
    return tabs

def _render_coupons_tab(user_email: str) -> None:
    st.markdown("### Cupons")
    st.caption("Área interna para criar, editar e acompanhar cupons. Visível só para usuários autorizados.")
    render_coupons_admin_section(current_user_email=user_email)



def render_client_area_page(user_id: str, user_name: str, user_email: str, credit_balance: Any) -> None:
    st.markdown("## Área do cliente")
    st.caption("Aqui ficam seus relatórios gerados, histórico de uso e ferramentas internas quando liberadas para o seu usuário.")

    should_render_checkout = bool(
        st.session_state.get("landing_checkout_mode")
        or st.session_state.get("payments_focus_mode")
        or st.session_state.get("current_payment_id")
        or st.session_state.get("current_payment_snapshot")
    )

    if should_render_checkout:
        selected_plan = st.session_state.get("landing_selected_plan_slug")

        title_col, action_col = st.columns([0.72, 0.28])
        with title_col:
            st.markdown("### Finalizar compra")
        with action_col:
            if st.button("❌ Cancelar / Fechar", use_container_width=True, key="client_area_close_checkout"):
                clear_all_checkout_states()
                st.rerun()

        if st.session_state.get("landing_checkout_mode") and selected_plan:
            st.caption(f"Você selecionou o plano {str(selected_plan).replace('_', ' ').title()} na landing. Gere o Pix abaixo para concluir a compra.")
        elif st.session_state.get("landing_checkout_mode"):
            st.caption("Você veio da landing. Escolha o plano e gere o Pix abaixo para concluir a compra.")
        elif st.session_state.get("current_payment_id") or st.session_state.get("current_payment_snapshot"):
            st.caption("Seu pagamento atual continua disponível abaixo até a conclusão ou fechamento manual.")
        else:
            st.caption("Escolha um plano para gerar o Pix.")

        from ui.payments_panel import render_payments_panel
        render_payments_panel()
        st.markdown("---")

    c1, c2, c3 = st.columns(3)
    with c1:
        _info_card("Nome", user_name or "—")
    with c2:
        _info_card("E-mail", user_email or "—")
    with c3:
        _info_card("Créditos", str(credit_balance if credit_balance is not None else "—"))

    tab_labels = _client_area_tabs_for_user(user_email)
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        _render_reports_tab(user_id)

    if len(tabs) > 1:
        with tabs[1]:
            _render_coupons_tab(user_email)
