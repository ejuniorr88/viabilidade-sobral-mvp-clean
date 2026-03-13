from __future__ import annotations

import hashlib
import io
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from core.auth import get_supabase_auth_client

REPORTS_TABLE = "client_reports"
REPORTS_BUCKET = "client-reports"
SIGNED_URL_EXPIRES_IN = 60 * 30


def _now_utc() -> datetime:
    return datetime.utcnow()


def _safe_name(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return "sem_nome"
    out = []
    for ch in raw:
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


def _pick(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _get_lot_front(calc: Dict[str, Any], session_state: Dict[str, Any]) -> float:
    return _to_float(
        _pick(
            session_state.get("lot_front_m"),
            session_state.get("lot_testada_m"),
            calc.get("lot_front_m"),
            calc.get("lot_testada_m"),
        ),
        0.0,
    )


def _get_lot_depth(calc: Dict[str, Any], session_state: Dict[str, Any]) -> float:
    return _to_float(
        _pick(
            session_state.get("lot_depth_m"),
            session_state.get("lot_profundidade_m"),
            calc.get("lot_depth_m"),
            calc.get("lot_profundidade_m"),
        ),
        0.0,
    )


def build_report_title(calc: Dict[str, Any], session_state: Dict[str, Any]) -> str:
    project_option = _pick(calc.get("selected_use_label"), calc.get("project_option"), calc.get("use_type_code"), "Relatório")
    zone = _pick(calc.get("zone"), calc.get("zone_label"), "Sem zona")
    road = _pick(calc.get("street_name"), calc.get("road_name"), "Sem rua")
    area = _to_float(_pick(session_state.get("lot_area_m2"), calc.get("lot_area_m2")), 0.0)
    area_text = f"{area:,.0f} m²".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{project_option} • {zone} • {road} • {area_text}"


def build_report_signature(calc: Dict[str, Any], session_state: Dict[str, Any], pdf_bytes: bytes) -> str:
    signature_payload = "|".join(
        [
            str(_pick(calc.get("use_type_code"), "")),
            str(_pick(calc.get("zone"), calc.get("zone_label"), "")),
            str(_pick(calc.get("street_name"), calc.get("road_name"), "")),
            str(_pick(session_state.get("lot_area_m2"), calc.get("lot_area_m2"), "")),
            str(_get_lot_front(calc, session_state)),
            str(_get_lot_depth(calc, session_state)),
            hashlib.sha256(pdf_bytes).hexdigest(),
        ]
    )
    return hashlib.sha256(signature_payload.encode("utf-8")).hexdigest()


def _build_storage_path(user_id: str, calc: Dict[str, Any]) -> Tuple[str, str]:
    now = _now_utc()
    zone = _safe_name(_pick(calc.get("zone"), calc.get("zone_label"), "sem_zona"))
    use_code = _safe_name(_pick(calc.get("use_type_code"), "relatorio"))
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
        .select("id, title, pdf_storage_path, pdf_file_name, created_at, report_signature")
        .eq("user_id", user_id)
        .eq("report_signature", report_signature)
        .limit(1)
        .execute()
    )
    rows = getattr(existing, "data", None) or []
    if rows:
        return {"ok": True, "already_exists": True, "report": rows[0]}

    storage_path, file_name = _build_storage_path(user_id, calc)
    storage_api = supabase.storage.from_(REPORTS_BUCKET)
    upload_errors: List[str] = []

    upload_attempts = [
        lambda: storage_api.upload(storage_path, pdf_bytes, {"content-type": "application/pdf", "upsert": "false"}),
        lambda: storage_api.upload(storage_path, pdf_bytes, file_options={"content-type": "application/pdf", "upsert": "false"}),
        lambda: storage_api.upload(storage_path, io.BytesIO(pdf_bytes), {"content-type": "application/pdf", "upsert": "false"}),
        lambda: storage_api.upload(storage_path, io.BytesIO(pdf_bytes), file_options={"content-type": "application/pdf", "upsert": "false"}),
    ]

    uploaded = False
    for attempt in upload_attempts:
        try:
            attempt()
            uploaded = True
            break
        except Exception as exc:
            upload_errors.append(str(exc))

    if not uploaded:
        raise RuntimeError("Falha ao salvar PDF no Storage: " + " | ".join(upload_errors[:2]))

    lot_area = _to_float(_pick(session_state.get("lot_area_m2"), calc.get("lot_area_m2")), 0.0)
    front = _get_lot_front(calc, session_state)
    depth = _get_lot_depth(calc, session_state)
    road_name = _pick(calc.get("street_name"), calc.get("road_name"))
    road_type = _pick(calc.get("street_class"), calc.get("road_type"))
    zone = _pick(calc.get("zone"), calc.get("zone_label"))

    payload = {
        "user_id": user_id,
        "user_email": user_email,
        "title": build_report_title(calc, session_state),
        "report_type": _pick(calc.get("use_type_code"), "urban_report"),
        "project_category": _pick(calc.get("categoria_label"), calc.get("project_category"), "Residencial"),
        "project_option": _pick(calc.get("selected_use_label"), calc.get("project_option"), calc.get("use_type_code")),
        "zone_code": zone,
        "zone_label": zone,
        "road_name": road_name,
        "road_type": road_type,
        "lot_area_m2": lot_area,
        "lot_front_m": front,
        "lot_depth_m": depth,
        "pdf_bucket": REPORTS_BUCKET,
        "pdf_storage_path": storage_path,
        "pdf_file_name": file_name,
        "pdf_size_bytes": len(pdf_bytes),
        "status": "saved",
        "report_signature": report_signature,
        "report_context": {
            "zone": zone,
            "road_name": road_name,
            "road_type": road_type,
            "project_option": _pick(calc.get("selected_use_label"), calc.get("project_option"), calc.get("use_type_code")),
            "lot_area_m2": lot_area,
            "lot_front_m": front,
            "lot_depth_m": depth,
            "saved_at_iso": _now_utc().isoformat(),
        },
    }

    inserted = supabase.table(REPORTS_TABLE).insert(payload).execute()
    row = (getattr(inserted, "data", None) or [{}])[0]
    return {"ok": True, "already_exists": False, "report": row}


def list_client_reports(user_id: str, limit: int = 30) -> List[Dict[str, Any]]:
    if not user_id:
        return []
    supabase = get_supabase_auth_client()
    response = (
        supabase.table(REPORTS_TABLE)
        .select(
            "id, title, user_email, report_type, project_category, project_option, zone_code, zone_label, road_name, road_type, lot_area_m2, lot_front_m, lot_depth_m, pdf_file_name, pdf_storage_path, created_at, status"
        )
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
