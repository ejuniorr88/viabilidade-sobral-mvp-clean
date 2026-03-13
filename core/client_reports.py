from __future__ import annotations

import hashlib
import io
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

import streamlit as st

from core.auth import get_supabase_auth_client

REPORTS_TABLE = "client_reports"
REPORTS_BUCKET = "client-reports"
SIGNED_URL_EXPIRES_IN = 60 * 30


def _now_utc() -> datetime:
    return datetime.utcnow()


def _safe_name(value: Any) -> str:
    s = str(value or "").strip()
    if not s:
        return "sem_nome"
    out = []
    for ch in s:
        if ch.isalnum() or ch in ("-", "_"):
            out.append(ch)
        elif ch in (" ", "/", "\\"):
            out.append("_")
    cleaned = "".join(out).strip("_")
    return cleaned[:80] or "sem_nome"


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _get_lot_front(calc: Dict[str, Any], session_state: Dict[str, Any]) -> float:
    return _to_float(
        session_state.get("lot_front_m")
        or session_state.get("lot_testada_m")
        or calc.get("lot_front_m")
        or calc.get("lot_testada_m"),
        0.0,
    )


def _get_lot_depth(calc: Dict[str, Any], session_state: Dict[str, Any]) -> float:
    return _to_float(
        session_state.get("lot_depth_m")
        or session_state.get("lot_profundidade_m")
        or calc.get("lot_depth_m")
        or calc.get("lot_profundidade_m"),
        0.0,
    )


def build_report_title(calc: Dict[str, Any], session_state: Dict[str, Any]) -> str:
    option = calc.get("selected_use_label") or calc.get("use_label") or calc.get("use_type_code") or "Relatório"
    zone = calc.get("zone") or "Sem zona"
    area = _to_float(session_state.get("lot_area_m2") or calc.get("lot_area_m2"), 0.0)
    return f"{option} - {zone} - {area:,.0f} m²".replace(",", "X").replace(".", ",").replace("X", ".")


def build_report_signature(calc: Dict[str, Any], session_state: Dict[str, Any], pdf_bytes: bytes) -> str:
    payload = "|".join(
        [
            str(calc.get("use_type_code") or ""),
            str(calc.get("zone") or ""),
            str(calc.get("road_name") or calc.get("street_name") or ""),
            str(session_state.get("lot_area_m2") or calc.get("lot_area_m2") or ""),
            str(_get_lot_front(calc, session_state)),
            str(_get_lot_depth(calc, session_state)),
            hashlib.sha256(pdf_bytes).hexdigest(),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _build_storage_path(user_id: str, calc: Dict[str, Any], session_state: Dict[str, Any]) -> tuple[str, str]:
    now = _now_utc()
    zone = _safe_name(calc.get("zone") or "sem_zona")
    use_code = _safe_name(calc.get("use_type_code") or "relatorio")
    stamp = now.strftime("%Y%m%d_%H%M%S")
    short_id = uuid4().hex[:8]
    file_name = f"report_{use_code}_{zone}_{stamp}_{short_id}.pdf"
    path = f"{user_id}/{now.strftime('%Y/%m')}/{file_name}"
    return path, file_name


def _extract_signed_url(result: Any) -> Optional[str]:
    if isinstance(result, dict):
        return result.get("signedURL") or result.get("signedUrl") or result.get("signed_url")
    signed = getattr(result, "signedURL", None) or getattr(result, "signedUrl", None) or getattr(result, "signed_url", None)
    if signed:
        return signed
    data = getattr(result, "data", None)
    if isinstance(data, dict):
        return data.get("signedURL") or data.get("signedUrl") or data.get("signed_url")
    return None


def save_client_report(
    *,
    user_id: str,
    user_email: str,
    calc: Dict[str, Any],
    session_state: Dict[str, Any],
    pdf_bytes: bytes,
) -> Dict[str, Any]:
    if not user_id:
        raise ValueError("Usuário não autenticado.")
    if not pdf_bytes:
        raise ValueError("PDF vazio.")

    supabase = get_supabase_auth_client()
    report_signature = build_report_signature(calc, session_state, pdf_bytes)

    existing = (
        supabase.table(REPORTS_TABLE)
        .select("id, pdf_storage_path, pdf_file_name, created_at")
        .eq("user_id", user_id)
        .eq("report_signature", report_signature)
        .limit(1)
        .execute()
    )
    rows = getattr(existing, "data", None) or []
    if rows:
        return {"ok": True, "already_exists": True, "report": rows[0]}

    storage_path, file_name = _build_storage_path(user_id, calc, session_state)

    upload_ok = False
    upload_errors: List[str] = []
    storage_api = supabase.storage.from_(REPORTS_BUCKET)

    upload_attempts = [
        lambda: storage_api.upload(
            storage_path,
            pdf_bytes,
            {"content-type": "application/pdf", "upsert": "false"},
        ),
        lambda: storage_api.upload(
            storage_path,
            pdf_bytes,
            file_options={"content-type": "application/pdf", "upsert": "false"},
        ),
        lambda: storage_api.upload(
            storage_path,
            io.BytesIO(pdf_bytes),
            {"content-type": "application/pdf", "upsert": "false"},
        ),
        lambda: storage_api.upload(
            storage_path,
            io.BytesIO(pdf_bytes),
            file_options={"content-type": "application/pdf", "upsert": "false"},
        ),
    ]

    for attempt in upload_attempts:
        try:
            attempt()
            upload_ok = True
            break
        except Exception as exc:
            upload_errors.append(str(exc))

    if not upload_ok:
        raise RuntimeError("Falha ao salvar PDF no Storage: " + " | ".join(upload_errors[:2]))

    payload = {
        "user_id": user_id,
        "user_email": user_email,
        "title": build_report_title(calc, session_state),
        "report_type": calc.get("use_type_code") or "REPORT",
        "project_category": calc.get("categoria_label") or calc.get("project_category") or "Residencial",
        "project_option": calc.get("selected_use_label") or calc.get("project_option") or calc.get("use_type_code"),
        "zone_code": calc.get("zone"),
        "zone_label": calc.get("zone"),
        "road_name": calc.get("street_name") or calc.get("road_name"),
        "road_type": calc.get("street_class") or calc.get("road_type"),
        "lot_area_m2": _to_float(session_state.get("lot_area_m2") or calc.get("lot_area_m2"), 0.0),
        "lot_front_m": _get_lot_front(calc, session_state),
        "lot_depth_m": _get_lot_depth(calc, session_state),
        "pdf_bucket": REPORTS_BUCKET,
        "pdf_storage_path": storage_path,
        "pdf_file_name": file_name,
        "pdf_size_bytes": len(pdf_bytes),
        "status": "saved",
        "report_signature": report_signature,
        "report_context": {
            "zone": calc.get("zone"),
            "street_name": calc.get("street_name") or calc.get("road_name"),
            "street_class": calc.get("street_class") or calc.get("road_type"),
            "use_type_code": calc.get("use_type_code"),
            "selected_use_label": calc.get("selected_use_label"),
            "lot_is_corner": bool(session_state.get("lot_is_corner") or calc.get("lot_is_corner")),
            "lot_is_irregular": bool(session_state.get("lot_is_irregular") or calc.get("lot_is_irregular")),
        },
    }

    response = supabase.table(REPORTS_TABLE).insert(payload).execute()
    inserted = (getattr(response, "data", None) or [{}])[0]
    return {"ok": True, "already_exists": False, "report": inserted}


def list_client_reports(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    if not user_id:
        return []
    supabase = get_supabase_auth_client()
    response = (
        supabase.table(REPORTS_TABLE)
        .select("id, title, report_type, project_option, zone_code, road_name, lot_area_m2, pdf_file_name, pdf_storage_path, created_at, status")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return getattr(response, "data", None) or []


def get_report_signed_url(storage_path: str, expires_in: int = SIGNED_URL_EXPIRES_IN) -> Optional[str]:
    if not storage_path:
        return None
    supabase = get_supabase_auth_client()
    result = supabase.storage.from_(REPORTS_BUCKET).create_signed_url(storage_path, expires_in)
    return _extract_signed_url(result)
