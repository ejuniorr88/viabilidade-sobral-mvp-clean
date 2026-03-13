from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

from core.client_reports import get_report_signed_url, list_client_reports


def _fmt_number(value: Any, suffix: str = "") -> str:
    try:
        number = float(value)
        return f"{number:,.2f}{suffix}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "—"


def _split_datetime(value: Optional[str]) -> tuple[str, str]:
    if not value:
        return "—", "—"
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y"), dt.strftime("%H:%M")
    except Exception:
        text = str(value).replace("T", " ")
        return text[:10], text[11:16] if len(text) >= 16 else "—"


def _render_user_cards(user_name: str, user_email: str, credit_balance: Any) -> None:
    st.markdown(
        f"""
        <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:10px 0 18px 0;">
          <div style="background:#fff;border:1px solid #e8e8e8;border-radius:16px;padding:14px 16px;">
            <div style="font-size:12px;color:#6b7280;margin-bottom:6px;">Nome</div>
            <div style="font-size:18px;font-weight:800;color:#1f2a44;">{user_name or '—'}</div>
          </div>
          <div style="background:#fff;border:1px solid #e8e8e8;border-radius:16px;padding:14px 16px;">
            <div style="font-size:12px;color:#6b7280;margin-bottom:6px;">E-mail</div>
            <div style="font-size:18px;font-weight:800;color:#1f2a44;word-break:break-word;">{user_email or '—'}</div>
          </div>
          <div style="background:#fff;border:1px solid #e8e8e8;border-radius:16px;padding:14px 16px;">
            <div style="font-size:12px;color:#6b7280;margin-bottom:6px;">Créditos</div>
            <div style="font-size:18px;font-weight:800;color:#1f2a44;">{credit_balance if credit_balance is not None else '—'}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_client_area_page(*, user_id: str, user_name: str, user_email: str, credit_balance: Any) -> None:
    st.markdown("## Área do cliente")
    st.caption("Aqui ficam seus relatórios gerados, com histórico e download a qualquer momento.")

    _render_user_cards(user_name=user_name, user_email=user_email, credit_balance=credit_balance)

    try:
        reports = list_client_reports(user_id=user_id, limit=30)
    except Exception as exc:
        st.error(f"Não foi possível carregar os relatórios da sua conta: {exc}")
        return

    if not reports:
        st.info("Você ainda não possui relatórios salvos. Quando gerar um relatório, ele será salvo automaticamente aqui.")
        return

    st.markdown("### Relatórios salvos")

    for idx, report in enumerate(reports):
        title = report.get("title") or report.get("project_option") or report.get("pdf_file_name") or f"Relatório {idx + 1}"
        zone = report.get("zone_label") or report.get("zone_code") or "—"
        road = report.get("road_name") or "—"
        date_text, time_text = _split_datetime(report.get("created_at"))
        storage_path = report.get("pdf_storage_path") or ""
        signed_url = None
        if storage_path:
            try:
                signed_url = get_report_signed_url(storage_path)
            except Exception:
                signed_url = None

        st.markdown(
            f"""
            <div style="background:#fff;border:1px solid #e8e8e8;border-radius:16px;padding:16px 18px;margin:10px 0 12px 0;">
              <div style="font-size:18px;font-weight:800;color:#1f2a44;">{title}</div>
              <div style="font-size:14px;color:#6b7280;margin-top:6px;">Zona: <strong>{zone}</strong> &nbsp; • &nbsp; Rua: <strong>{road}</strong></div>
              <div style="font-size:14px;color:#6b7280;margin-top:6px;">Data: <strong>{date_text}</strong> &nbsp; • &nbsp; Horário: <strong>{time_text}</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2, c3, c4 = st.columns([1.2, 1.4, 1.1, 4.3])
        with c1:
            st.text_input("Zona", value=str(zone), key=f"client_zone_{idx}", disabled=True)
        with c2:
            st.text_input("Rua", value=str(road), key=f"client_road_{idx}", disabled=True)
        with c3:
            st.text_input("Horário", value=str(time_text), key=f"client_time_{idx}", disabled=True)
        with c4:
            if signed_url:
                st.link_button("⬇️ Fazer download", signed_url, use_container_width=True)
            else:
                st.button("⬇️ Fazer download", key=f"client_download_disabled_{idx}", disabled=True, use_container_width=True)
