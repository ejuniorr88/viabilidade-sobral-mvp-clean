from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List
from zoneinfo import ZoneInfo

import streamlit as st
from supabase import Client, create_client

from core.env_secrets import get_secret_str

_BUCKET = "client-reports"
_TZ = ZoneInfo("America/Fortaleza")


def _read_secret(key: str) -> str:
    value = get_secret_str(key, required=True)
    if value:
        return value
    raise RuntimeError(f"Secret/variável ausente: {key}")


@st.cache_resource(show_spinner=False)
def get_supabase_service_client() -> Client:
    url = _read_secret("SUPABASE_URL")
    key = get_secret_str("SUPABASE_SERVICE_ROLE_KEY")
    if not key:
        key = _read_secret("SUPABASE_ANON_KEY")
    return create_client(url, key)


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_number(value: Any, decimals: int = 2) -> float:
    try:
        return round(float(value), decimals)
    except Exception:
        return 0.0


def _pick_value(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and value.strip() == "":
            continue
        return value
    return None


def _pick_bool(*values: Any) -> bool:
    for value in values:
        if value is None:
            continue
        return bool(value)
    return False


def _safe_local_now() -> datetime:
    return datetime.now(_TZ)


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    try:
        json.dumps(value, ensure_ascii=False, default=str)
        return value
    except Exception:
        return str(value)


def _build_title(calc: Dict[str, Any], session_state: Dict[str, Any]) -> str:
    project = _normalize_text(
        calc.get("selected_use_label")
        or calc.get("categoria_label")
        or calc.get("use_type_code")
        or "Relatório"
    )
    zone = _normalize_text(calc.get("zone") or calc.get("zone_label") or "—")
    road = _normalize_text(calc.get("street_name") or calc.get("road_name") or calc.get("logradouro") or "Sem rua")
    area = _normalize_number(session_state.get("lot_area_m2") or calc.get("lot_area_m2"))
    return f"{project} • {zone} • {road} • {area:.0f} m²"


def build_report_signature(calc: Dict[str, Any], session_state: Dict[str, Any]) -> str:
    payload = {
        "use_type_code": _normalize_text(calc.get("use_type_code")),
        "selected_use_label": _normalize_text(calc.get("selected_use_label")),
        "categoria_label": _normalize_text(calc.get("categoria_label")),
        "zone": _normalize_text(calc.get("zone") or calc.get("zone_sigla") or calc.get("zone_label")),
        "road_name": _normalize_text(calc.get("street_name") or calc.get("road_name") or calc.get("logradouro")),
        "road_type": _normalize_text(calc.get("road_type") or calc.get("via_type")),
        "project_mode": _normalize_text(calc.get("project_mode")),
        "lot_area_m2": _normalize_number(_pick_value(session_state.get("lot_area_m2"), calc.get("lot_area_m2"))),
        "built_ground_m2": _normalize_number(
            _pick_value(
                session_state.get("built_ground_m2"),
                session_state.get("built_ground_input_m2"),
                calc.get("built_ground_m2"),
                calc.get("built_ground_input_m2"),
            )
        ),
        "permeable_area_m2": _normalize_number(
            _pick_value(
                session_state.get("permeable_area_m2"),
                session_state.get("area_permeavel_prevista_m2"),
                calc.get("permeable_area_m2"),
                calc.get("area_permeavel_prevista_m2"),
            )
        ),
        "lot_front_m": _normalize_number(
            _pick_value(
                session_state.get("lot_front_m"),
                session_state.get("lot_testada_m"),
                calc.get("lot_front_m"),
                calc.get("lot_testada_m"),
            )
        ),
        "lot_depth_m": _normalize_number(
            _pick_value(
                session_state.get("lot_depth_m"),
                session_state.get("lot_profundidade_m"),
                calc.get("lot_depth_m"),
                calc.get("lot_profundidade_m"),
            )
        ),
        "lot_is_corner": _pick_bool(session_state.get("lot_is_corner"), calc.get("lot_is_corner")),
        "lot_is_irregular": _pick_bool(
            session_state.get("lot_is_irregular"),
            calc.get("lot_is_irregular"),
            calc.get("lot_irregular"),
        ),
        "selected_lat": _normalize_number(_pick_value(calc.get("selected_lat"), st.session_state.get("selected_lat")), 6),
        "selected_lon": _normalize_number(_pick_value(calc.get("selected_lon"), st.session_state.get("selected_lon")), 6),
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _storage_path(user_id: str, report_signature: str) -> str:
    now = _safe_local_now()
    return f"{user_id}/{now:%Y}/{now:%m}/report_{report_signature[:20]}.pdf"


def _build_report_context(
    *,
    user_email: str,
    calc: Dict[str, Any],
    session_state: Dict[str, Any],
    pdf_bytes: bytes,
    signature: str,
    storage_path: str,
    file_name: str,
    local_now: datetime,
) -> Dict[str, Any]:
    road_name = _normalize_text(calc.get("street_name") or calc.get("road_name") or calc.get("logradouro"))
    zone = _normalize_text(calc.get("zone") or calc.get("zone_label"))
    return {
        "saved_at_local": local_now.isoformat(),
        "saved_at_label": local_now.strftime("%d/%m/%Y %H:%M"),
        "viewer_version": "inline_report_snapshot_v1",
        "title": _build_title(calc, session_state),
        "user_email": _normalize_text(user_email),
        "report_type": "urban_report",
        "project_category": _normalize_text(calc.get("categoria_label")),
        "project_option": _normalize_text(calc.get("selected_use_label")),
        "zone_code": zone,
        "zone_label": zone,
        "road_name": road_name,
        "road_type": _normalize_text(calc.get("road_type") or calc.get("via_type")),
        "lot_area_m2": _normalize_number(session_state.get("lot_area_m2") or calc.get("lot_area_m2")),
        "pdf_bucket": _BUCKET,
        "pdf_storage_path": storage_path,
        "pdf_file_name": file_name,
        "pdf_size_bytes": len(pdf_bytes),
        "status": "saved",
        "report_signature": signature,
        "inputs_snapshot": {
            "project_mode": _normalize_text(calc.get("project_mode")),
            "built_ground_m2": _normalize_number(
                _pick_value(
                    session_state.get("built_ground_m2"),
                    session_state.get("built_ground_input_m2"),
                    calc.get("built_ground_m2"),
                    calc.get("built_ground_input_m2"),
                )
            ),
            "permeable_area_m2": _normalize_number(
                _pick_value(
                    session_state.get("permeable_area_m2"),
                    session_state.get("area_permeavel_prevista_m2"),
                    calc.get("permeable_area_m2"),
                    calc.get("area_permeavel_prevista_m2"),
                )
            ),
            "lot_front_m": _normalize_number(
                _pick_value(
                    session_state.get("lot_front_m"),
                    session_state.get("lot_testada_m"),
                    calc.get("lot_front_m"),
                    calc.get("lot_testada_m"),
                )
            ),
            "lot_depth_m": _normalize_number(
                _pick_value(
                    session_state.get("lot_depth_m"),
                    session_state.get("lot_profundidade_m"),
                    calc.get("lot_depth_m"),
                    calc.get("lot_profundidade_m"),
                )
            ),
        },
        "calc_snapshot": _json_safe(calc),
        "session_snapshot": _json_safe(session_state),
    }


def _with_display_aliases(row: Dict[str, Any]) -> Dict[str, Any]:
    """Keep the UI contract without requiring presentation columns in client_reports."""
    if not isinstance(row, dict):
        return row
    out = dict(row)
    ctx = out.get("report_context") or {}
    if not isinstance(ctx, dict):
        ctx = {}

    out.setdefault("title", ctx.get("title") or "Relatório salvo")
    out.setdefault("zone_label", ctx.get("zone_label") or ctx.get("zone_code") or "—")
    out.setdefault("road_name", ctx.get("road_name") or "—")
    out.setdefault("pdf_bucket", ctx.get("pdf_bucket") or _BUCKET)
    out.setdefault("pdf_storage_path", ctx.get("pdf_storage_path") or ctx.get("file_path") or "")
    out.setdefault("pdf_file_name", ctx.get("pdf_file_name") or "")
    out.setdefault("status", ctx.get("status") or "saved")
    return out


def save_client_report(
    user_id: str,
    user_email: str,
    calc: Dict[str, Any],
    session_state: Dict[str, Any],
    pdf_bytes: bytes,
    report_signature: str | None = None,
) -> Dict[str, Any]:
    if not user_id:
        raise RuntimeError("Usuário não identificado para salvar relatório.")
    if not pdf_bytes:
        raise RuntimeError("PDF vazio. Nada para salvar.")

    client = get_supabase_service_client()
    signature = report_signature or build_report_signature(calc, session_state)

    # Schema real consolidado: não selecionar colunas de apresentação/storage diretas.
    existing = (
        client.table("client_reports")
        .select("id,user_id,report_signature,report_context,created_at")
        .eq("user_id", user_id)
        .eq("report_signature", signature)
        .limit(1)
        .execute()
    )
    if existing.data:
        return {"ok": True, "already_exists": True, "row": _with_display_aliases(existing.data[0])}

    storage_path = _storage_path(user_id, signature)
    file_name = storage_path.rsplit("/", 1)[-1]

    upload_error = None
    try:
        client.storage.from_(_BUCKET).upload(
            path=storage_path,
            file=pdf_bytes,
            file_options={"content-type": "application/pdf", "upsert": False},
        )
    except Exception as exc:
        upload_error = exc

    if upload_error is not None:
        message = str(upload_error).lower()
        if "already exists" not in message and "duplicate" not in message and "409" not in message:
            raise RuntimeError(f"Falha ao salvar PDF no Storage: {upload_error}")

    local_now = _safe_local_now()
    report_context = _build_report_context(
        user_email=user_email,
        calc=calc,
        session_state=session_state,
        pdf_bytes=pdf_bytes,
        signature=signature,
        storage_path=storage_path,
        file_name=file_name,
        local_now=local_now,
    )

    # Não incluir file_path nem outras colunas que podem não existir no Supabase real.
    row = {
        "user_id": user_id,
        "report_signature": signature,
        "report_context": report_context,
    }

    try:
        inserted = client.table("client_reports").insert(row).execute()
        if inserted.data:
            return {"ok": True, "already_exists": False, "row": _with_display_aliases(inserted.data[0])}
        return {"ok": True, "already_exists": False, "row": _with_display_aliases({**row, "created_at": local_now.isoformat()})}
    except Exception as exc:
        msg = str(exc).lower()
        if "duplicate key" in msg or "already exists" in msg or "23505" in msg:
            existing = (
                client.table("client_reports")
                .select("id,user_id,report_signature,report_context,created_at")
                .eq("user_id", user_id)
                .eq("report_signature", signature)
                .limit(1)
                .execute()
            )
            fallback_row = _with_display_aliases({**row, "created_at": local_now.isoformat()})
            return {
                "ok": True,
                "already_exists": True,
                "row": _with_display_aliases(existing.data[0]) if existing.data else fallback_row,
            }
        raise RuntimeError(f"Falha ao registrar relatório no banco: {exc}")


def list_client_reports(user_id: str) -> List[Dict[str, Any]]:
    client = get_supabase_service_client()
    result = (
        client.table("client_reports")
        .select("id,user_id,report_signature,report_context,created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [_with_display_aliases(row) for row in (result.data or [])]


def build_download_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    if not storage_path:
        return ""
    client = get_supabase_service_client()
    data = client.storage.from_(_BUCKET).create_signed_url(storage_path, expires_in)
    if isinstance(data, dict):
        return data.get("signedURL") or data.get("signedUrl") or ""
    return ""
