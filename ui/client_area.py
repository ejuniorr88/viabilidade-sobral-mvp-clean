from __future__ import annotations

from datetime import datetime
from typing import Any, Dict
from zoneinfo import ZoneInfo

import streamlit as st

from core.client_reports import build_download_signed_url, list_client_reports
from ui.coupons_admin import render_coupons_admin_section

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

        a, b, c, d = st.columns([1.1, 1.3, 1.0, 4.0])
        with a:
            st.text_input("Zona", value=zone, disabled=True, key=f"zone_{item.get('id')}")
        with b:
            st.text_input("Rua", value=road, disabled=True, key=f"road_{item.get('id')}")
        with c:
            st.text_input("Horário", value=time_label, disabled=True, key=f"time_{item.get('id')}")
        with d:
            signed_url = ""
            try:
                signed_url = build_download_signed_url(path)
            except Exception:
                signed_url = ""
            if signed_url:
                st.link_button("⬇️ Fazer download", signed_url, use_container_width=True)
            else:
                st.button("⬇️ Fazer download", disabled=True, use_container_width=True, key=f"download_disabled_{item.get('id')}")


def _render_coupons_tab(user_email: str) -> None:
    st.markdown("### Cupons")
    st.caption("Área interna para criar, editar e acompanhar cupons. Visível só para usuários autorizados.")
    render_coupons_admin_section(current_user_email=user_email)


def render_client_area_page(user_id: str, user_name: str, user_email: str, credit_balance: Any) -> None:
    st.markdown("## Área do cliente")
    st.caption("Aqui ficam seus relatórios gerados, histórico de uso e ferramentas internas quando liberadas para o seu usuário.")

    c1, c2, c3 = st.columns(3)
    with c1:
        _info_card("Nome", user_name or "—")
    with c2:
        _info_card("E-mail", user_email or "—")
    with c3:
        _info_card("Créditos", str(credit_balance if credit_balance is not None else "—"))

    tab_reports, tab_coupons = st.tabs(["Relatórios", "Cupons"])

    with tab_reports:
        _render_reports_tab(user_id)

    with tab_coupons:
        _render_coupons_tab(user_email)
