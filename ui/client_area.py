from __future__ import annotations

from typing import Any, Dict, List, Optional

import streamlit as st

from core.client_reports import get_report_signed_url, list_client_reports


def _fmt_datetime(value: Optional[str]) -> str:
    if not value:
        return "—"
    try:
        return str(value).replace("T", " ")[:16]
    except Exception:
        return str(value)


def _fmt_area(value: Any) -> str:
    try:
        area = float(value or 0)
        return f"{area:,.2f} m²".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "—"


def _build_meta_line(report: Dict[str, Any]) -> str:
    parts = []
    if report.get("project_option"):
        parts.append(str(report.get("project_option")))
    if report.get("zone_code"):
        parts.append(f"Zona: {report.get('zone_code')}")
    if report.get("road_name"):
        parts.append(str(report.get("road_name")))
    return " • ".join(parts) if parts else "—"


def render_client_area(user_id: str) -> None:
    st.markdown("### Área do cliente")
    st.caption("Seus relatórios salvos ficam vinculados à sua conta e podem ser abertos depois.")

    try:
        reports = list_client_reports(user_id, limit=20)
    except Exception as e:
        st.warning(f"Não foi possível carregar os relatórios salvos: {e}")
        return

    if not reports:
        st.info("Você ainda não possui relatórios salvos na área do cliente.")
        return

    for idx, report in enumerate(reports):
        title = report.get("title") or report.get("pdf_file_name") or f"Relatório {idx + 1}"
        meta = _build_meta_line(report)
        created_at = _fmt_datetime(report.get("created_at"))
        area = _fmt_area(report.get("lot_area_m2"))
        status = report.get("status") or "—"
        storage_path = report.get("pdf_storage_path") or ""

        st.markdown(
            f"""
            <div style="border:1px solid #e7e7e7;border-radius:14px;padding:14px 16px;background:#fff;margin-bottom:10px;">
                <div style="font-size:18px;font-weight:800;color:#1f2a44;">{title}</div>
                <div style="font-size:13px;color:#6b7280;margin-top:4px;">{meta}</div>
                <div style="font-size:13px;color:#6b7280;margin-top:6px;">Data: {created_at} • Área do lote: {area} • Status: {status}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns([1, 1, 3])
        with c1:
            if storage_path:
                if st.button("🔗 Abrir", key=f"open_saved_report_{idx}", use_container_width=True):
                    try:
                        url = get_report_signed_url(storage_path)
                        if url:
                            st.link_button("Abrir relatório agora", url, use_container_width=True)
                        else:
                            st.warning("Não foi possível gerar o link do relatório.")
                    except Exception as e:
                        st.warning(f"Não foi possível abrir o relatório: {e}")
            else:
                st.button("🔗 Abrir", key=f"open_saved_report_{idx}", disabled=True, use_container_width=True)
        with c2:
            if storage_path:
                if st.button("⬇️ Link", key=f"download_saved_report_{idx}", use_container_width=True):
                    try:
                        url = get_report_signed_url(storage_path)
                        if url:
                            st.link_button("Baixar relatório agora", url, use_container_width=True)
                        else:
                            st.warning("Não foi possível gerar o link do relatório.")
                    except Exception as e:
                        st.warning(f"Não foi possível gerar o link de download: {e}")
            else:
                st.button("⬇️ Link", key=f"download_saved_report_{idx}", disabled=True, use_container_width=True)
        with c3:
            st.write("")
