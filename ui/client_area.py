from __future__ import annotations

from copy import deepcopy
import json
from datetime import datetime
from typing import Any, Dict
from zoneinfo import ZoneInfo

import streamlit as st

from core.client_reports import build_download_signed_url, list_client_reports
from core import snapshot_pdf as snapshot_pdf_module
from core.coupons import user_can_manage_coupons
from ui.coupons_admin import render_coupons_admin_section
from ui.relatorio import render_relatorio_section

_TZ = ZoneInfo("America/Fortaleza")


def _report_context(item: Dict[str, Any]) -> Dict[str, Any]:
    value = item.get("report_context")
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _first_present(*values: Any, default: str = "—") -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return default



def _deep_pick(mapping: Any, keys: tuple[str, ...], *, max_depth: int = 4) -> Any:
    if not isinstance(mapping, dict) or max_depth < 0:
        return None
    for key in keys:
        value = mapping.get(key)
        if value is not None and not (isinstance(value, str) and value.strip() == ""):
            return value
    for value in mapping.values():
        if isinstance(value, dict):
            found = _deep_pick(value, keys, max_depth=max_depth - 1)
            if found is not None and not (isinstance(found, str) and str(found).strip() == ""):
                return found
    return None


def _extract_zone_from_context(ctx: Dict[str, Any], item: Dict[str, Any]) -> str:
    calc_snapshot = ctx.get("calc_snapshot") if isinstance(ctx.get("calc_snapshot"), dict) else {}
    session_snapshot = ctx.get("session_snapshot") if isinstance(ctx.get("session_snapshot"), dict) else {}
    session_calc = session_snapshot.get("calc") if isinstance(session_snapshot.get("calc"), dict) else {}
    return _first_present(
        item.get("zone_label"),
        item.get("zone_code"),
        item.get("zone"),
        ctx.get("zone_label"),
        ctx.get("zone_code"),
        ctx.get("zone"),
        calc_snapshot.get("zone"),
        calc_snapshot.get("zone_sigla"),
        calc_snapshot.get("zone_display_label"),
        calc_snapshot.get("zone_label"),
        calc_snapshot.get("zone_lookup"),
        session_calc.get("zone"),
        session_calc.get("zone_sigla"),
        session_calc.get("zone_display_label"),
        _deep_pick(calc_snapshot, ("zone", "zone_sigla", "zone_display_label", "zone_label", "zone_code", "zone_lookup")),
    )


def _extract_road_from_context(ctx: Dict[str, Any], item: Dict[str, Any]) -> str:
    calc_snapshot = ctx.get("calc_snapshot") if isinstance(ctx.get("calc_snapshot"), dict) else {}
    session_snapshot = ctx.get("session_snapshot") if isinstance(ctx.get("session_snapshot"), dict) else {}
    session_calc = session_snapshot.get("calc") if isinstance(session_snapshot.get("calc"), dict) else {}
    return _first_present(
        item.get("road_name"),
        item.get("via_nome"),
        item.get("street_name"),
        item.get("logradouro"),
        ctx.get("road_name"),
        ctx.get("via_nome"),
        ctx.get("street_name"),
        ctx.get("logradouro"),
        calc_snapshot.get("street_name"),
        calc_snapshot.get("via_nome"),
        calc_snapshot.get("road_name"),
        calc_snapshot.get("logradouro"),
        session_calc.get("street_name"),
        session_calc.get("via_nome"),
        session_calc.get("road_name"),
        session_calc.get("logradouro"),
        _deep_pick(calc_snapshot, ("street_name", "via_nome", "road_name", "logradouro")),
    )

def _to_local_label(item: Dict[str, Any]) -> tuple[str, str]:
    ctx = _report_context(item)
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
    ctx = _report_context(item)
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


def _render_snapshot_downloads(item: Dict[str, Any]) -> None:
    ctx = _report_context(item)
    calc_snapshot = ctx.get("calc_snapshot") if isinstance(ctx.get("calc_snapshot"), dict) else {}
    if not calc_snapshot:
        return

    required_helpers = (
        "generate_snapshot_html_bytes",
        "generate_snapshot_pdf_bytes",
        "snapshot_file_stem",
        "snapshot_pdf_renderer_available",
    )
    missing_helpers = [name for name in required_helpers if not hasattr(snapshot_pdf_module, name)]
    if missing_helpers:
        st.warning(
            "O módulo de PDF visual do snapshot está incompleto no deploy. "
            "Substitua também o arquivo core/snapshot_pdf.py do mesmo patch para liberar esta função."
        )
        return

    file_stem = snapshot_pdf_module.snapshot_file_stem(item)

    try:
        html_bytes = snapshot_pdf_module.generate_snapshot_html_bytes(item)
        st.download_button(
            label="⬇️ Baixar HTML visual do snapshot para imprimir em PDF",
            data=html_bytes,
            file_name=f"{file_stem}.html",
            mime="text/html",
            use_container_width=True,
            key=f"download_snapshot_html_{item.get('id')}",
        )
    except Exception as html_exc:
        st.warning(f"Não foi possível gerar o HTML visual do snapshot: {html_exc}")
        return

    if not snapshot_pdf_module.snapshot_pdf_renderer_available():
        st.info(
            "PDF visual automático indisponível neste ambiente. Para não gerar um arquivo incompleto, "
            "use o HTML visual do snapshot e imprima/salve em PDF pelo navegador."
        )
        return

    try:
        visual_pdf_bytes = snapshot_pdf_module.generate_snapshot_pdf_bytes(item)
        st.download_button(
            label="⬇️ Baixar PDF visual do snapshot",
            data=visual_pdf_bytes,
            file_name=f"{file_stem}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"download_snapshot_pdf_{item.get('id')}",
        )
    except getattr(snapshot_pdf_module, "SnapshotPdfUnavailable", RuntimeError) as exc:
        st.info(str(exc))
    except Exception as exc:
        st.warning(f"Não foi possível gerar o PDF visual do snapshot real: {exc}")

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
        ctx = _report_context(item)
        calc_snapshot = ctx.get("calc_snapshot") if isinstance(ctx.get("calc_snapshot"), dict) else {}
        session_snapshot = ctx.get("session_snapshot") if isinstance(ctx.get("session_snapshot"), dict) else {}

        title = _first_present(
            item.get("title"),
            ctx.get("title"),
            default="Relatório salvo",
        )
        zone = _extract_zone_from_context(ctx, item)
        road = _extract_road_from_context(ctx, item)
        path = _first_present(
            item.get("pdf_storage_path"),
            item.get("file_path"),
            ctx.get("pdf_storage_path"),
            ctx.get("file_path"),
            default="",
        )
        bucket = _first_present(
            item.get("pdf_bucket"),
            ctx.get("pdf_bucket"),
            default="",
        )

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
                signed_url = build_download_signed_url(path, bucket=bucket)
            except Exception:
                signed_url = ""
            if signed_url:
                st.link_button("⬇️ Fazer download", signed_url, use_container_width=True)
            else:
                st.button("⬇️ Fazer download", disabled=True, use_container_width=True, key=f"download_disabled_{item.get('id')}")

        if st.session_state.get(_PREVIEW_REPORT_KEY) == item.get("id"):
            _render_saved_report_preview(item)
            _render_snapshot_downloads(item)


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
