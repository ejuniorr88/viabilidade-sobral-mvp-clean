from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Any, Dict, List
from zoneinfo import ZoneInfo

import streamlit as st
from supabase import Client, create_client

from core.env_secrets import get_secret_str

_DEFAULT_BUCKET = "client-reports"
_FALLBACK_BUCKETS = ("client-reports", "relatorio")
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


def _extract_selected_coords(calc: Dict[str, Any], session_state: Dict[str, Any]) -> tuple[Any, Any]:
    """Retorna a coordenada consolidada usada na assinatura salva do relatório.

    No salvamento, ``calc["lat"]``/``calc["lon"]`` representam o cálculo já
    executado. O ``last_click`` entra apenas como fallback para cenários legados
    onde o snapshot ainda não levou coordenadas para o calc.
    """
    session_calc = session_state.get("calc") if isinstance(session_state.get("calc"), dict) else {}
    last_click = session_state.get("last_click")
    click_lat = click_lon = None
    if isinstance(last_click, dict):
        click_lat = last_click.get("lat")
        click_lon = last_click.get("lon")

    return (
        _pick_value(
            calc.get("lat"),
            calc.get("selected_lat"),
            session_calc.get("lat"),
            session_state.get("lat"),
            click_lat,
            session_calc.get("selected_lat"),
            session_state.get("selected_lat"),
        ),
        _pick_value(
            calc.get("lon"),
            calc.get("selected_lon"),
            session_calc.get("lon"),
            session_state.get("lon"),
            click_lon,
            session_calc.get("selected_lon"),
            session_state.get("selected_lon"),
        ),
    )


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


def _extract_zone(calc: Dict[str, Any], session_state: Dict[str, Any] | None = None) -> str:
    session_state = session_state or {}
    session_calc = session_state.get("calc") if isinstance(session_state.get("calc"), dict) else {}
    zone_keys = ("zone", "zone_sigla", "zone_display_label", "zone_label", "zone_code", "zone_lookup")
    return _normalize_text(
        _pick_value(
            *(calc.get(k) for k in zone_keys),
            *(session_calc.get(k) for k in zone_keys),
            *(session_state.get(k) for k in zone_keys),
            _deep_pick(calc, zone_keys),
            _deep_pick(session_calc, zone_keys),
            _deep_pick(session_state, zone_keys),
        )
    )


def _extract_subzone(calc: Dict[str, Any], session_state: Dict[str, Any] | None = None) -> str:
    session_state = session_state or {}
    session_calc = session_state.get("calc") if isinstance(session_state.get("calc"), dict) else {}
    keys = ("subzone_code", "subzona", "subzone", "setor")
    return _normalize_text(
        _pick_value(
            *(calc.get(k) for k in keys),
            *(session_calc.get(k) for k in keys),
            *(session_state.get(k) for k in keys),
            _deep_pick(calc, keys),
            _deep_pick(session_calc, keys),
            _deep_pick(session_state, keys),
        )
    )


def _extract_road(calc: Dict[str, Any], session_state: Dict[str, Any] | None = None) -> str:
    session_state = session_state or {}
    session_calc = session_state.get("calc") if isinstance(session_state.get("calc"), dict) else {}
    road_keys = ("street_name", "via_nome", "road_name", "logradouro", "road_label")
    return _normalize_text(
        _pick_value(
            *(calc.get(k) for k in road_keys),
            *(session_calc.get(k) for k in road_keys),
            *(session_state.get(k) for k in road_keys),
            _deep_pick(calc, road_keys),
            _deep_pick(session_calc, road_keys),
            _deep_pick(session_state, road_keys),
        )
    )


def _extract_road_type(calc: Dict[str, Any], session_state: Dict[str, Any] | None = None) -> str:
    session_state = session_state or {}
    session_calc = session_state.get("calc") if isinstance(session_state.get("calc"), dict) else {}
    keys = (
        "road_type",
        "via_type",
        "via_tipo",
        "street_type",
        "tipo_via",
        "road_class",
        "via_classificacao",
        "via_tipo_txt",
    )
    return _normalize_text(
        _pick_value(
            *(calc.get(k) for k in keys),
            *(session_calc.get(k) for k in keys),
            *(session_state.get(k) for k in keys),
            _deep_pick(calc, keys),
            _deep_pick(session_calc, keys),
            _deep_pick(session_state, keys),
        )
    )


def _extract_status_marker(calc: Dict[str, Any], session_state: Dict[str, Any] | None = None) -> str:
    session_state = session_state or {}
    session_calc = session_state.get("calc") if isinstance(session_state.get("calc"), dict) else {}
    keys = (
        "status_curto",
        "final_status",
        "resultado_final",
        "viability_status",
        "viabilidade_status",
        "zone_class",
        "via_class",
        "adequabilidade_zona",
        "adequabilidade_via",
    )
    values: list[str] = []
    for source in (calc, session_calc, session_state):
        if not isinstance(source, dict):
            continue
        for key in keys:
            value = source.get(key)
            if value is not None and not (isinstance(value, str) and value.strip() == ""):
                values.append(str(value).strip())
        found = _deep_pick(source, keys)
        if found is not None and not (isinstance(found, str) and str(found).strip() == ""):
            values.append(str(found).strip())
    return "|".join(dict.fromkeys(values))


def _ctx(item: Dict[str, Any]) -> Dict[str, Any]:
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


def _build_title(calc: Dict[str, Any], session_state: Dict[str, Any]) -> str:
    project = _normalize_text(
        calc.get("selected_use_label")
        or calc.get("categoria_label")
        or calc.get("use_type_code")
        or "Relatório"
    )
    zone = _extract_zone(calc, session_state) or "—"
    road = _extract_road(calc, session_state) or "Sem rua"
    area = _normalize_number(session_state.get("lot_area_m2") or calc.get("lot_area_m2"))
    return f"{project} • {zone} • {road} • {area:.0f} m²"


def build_report_signature(calc: Dict[str, Any], session_state: Dict[str, Any]) -> str:
    selected_lat, selected_lon = _extract_selected_coords(calc, session_state)

    payload = {
        "use_type_code": _normalize_text(calc.get("use_type_code")),
        "selected_use_label": _normalize_text(calc.get("selected_use_label")),
        "categoria_label": _normalize_text(calc.get("categoria_label")),
        # Alguns cenários, especialmente “possível pela via”, guardam zona/via
        # no snapshot de sessão e não diretamente no calc. Usar os extratores
        # evita colisão de assinatura e falso already_exists/estorno.
        "zone": _extract_zone(calc, session_state),
        "subzone": _extract_subzone(calc, session_state),
        "road_name": _extract_road(calc, session_state),
        "road_type": _extract_road_type(calc, session_state),
        "status_marker": _extract_status_marker(calc, session_state),
        "project_mode": _normalize_text(_pick_value(calc.get("project_mode"), session_state.get("project_mode"))),
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
        "lot_is_midblock": _pick_bool(session_state.get("lot_is_midblock"), calc.get("lot_is_midblock")),
        "lot_is_irregular": _pick_bool(
            session_state.get("lot_is_irregular"),
            calc.get("lot_is_irregular"),
            calc.get("lot_irregular"),
        ),
        "lot_type_label": _normalize_text(_pick_value(session_state.get("lot_type_label"), calc.get("lot_type_label"))),
        "selected_lat": _normalize_number(selected_lat, 6),
        "selected_lon": _normalize_number(selected_lon, 6),
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _storage_path(user_id: str, report_signature: str) -> str:
    now = _safe_local_now()
    return f"{user_id}/{now:%Y}/{now:%m}/report_{report_signature[:20]}.pdf"


def _configured_buckets() -> List[str]:
    configured = _normalize_text(get_secret_str("CLIENT_REPORTS_BUCKET")) or _DEFAULT_BUCKET
    buckets: List[str] = []
    for bucket in (configured, *_FALLBACK_BUCKETS):
        if bucket and bucket not in buckets:
            buckets.append(bucket)
    return buckets


def _upload_pdf(client: Client, storage_path: str, pdf_bytes: bytes) -> str:
    last_error: Exception | None = None
    for bucket in _configured_buckets():
        try:
            client.storage.from_(bucket).upload(
                path=storage_path,
                file=pdf_bytes,
                file_options={"content-type": "application/pdf", "upsert": False},
            )
            return bucket
        except Exception as exc:
            message = str(exc).lower()
            if "already exists" in message or "duplicate" in message or "409" in message:
                return bucket
            last_error = exc
    raise RuntimeError(f"Falha ao salvar PDF no Storage: {last_error}")


def _report_context(
    *,
    calc: Dict[str, Any],
    session_state: Dict[str, Any],
    user_email: str,
    signature: str,
    storage_path: str,
    user_name: str = "",
    bucket: str,
    pdf_bytes: bytes,
) -> Dict[str, Any]:
    local_now = _safe_local_now()
    road_name = _extract_road(calc, session_state)
    zone = _extract_zone(calc, session_state)
    file_name = storage_path.rsplit("/", 1)[-1]
    return {
        "saved_at_local": local_now.isoformat(),
        "saved_at_label": local_now.strftime("%d/%m/%Y %H:%M"),
        "viewer_version": "inline_report_snapshot_v1",
        "user_email": _normalize_text(user_email),
        "user_name": _normalize_text(user_name or session_state.get("auth_user_name") or session_state.get("auth_name")),
        "title": _build_title(calc, session_state),
        "report_type": "urban_report",
        "project_category": _normalize_text(calc.get("categoria_label")),
        "project_option": _normalize_text(calc.get("selected_use_label")),
        "zone_code": zone,
        "zone_label": zone,
        "road_name": road_name,
        "road_type": _extract_road_type(calc, session_state),
        "lot_area_m2": _normalize_number(session_state.get("lot_area_m2") or calc.get("lot_area_m2")),
        "pdf_bucket": bucket,
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


def _minimal_row(user_id: str, signature: str, report_context: Dict[str, Any]) -> Dict[str, Any]:
    # Regra de segurança: gravar somente colunas consolidadas/minimamente necessárias.
    # Os metadados variáveis ficam dentro de report_context para evitar quebrar quando
    # o schema real do Supabase não tiver colunas como title/pdf_storage_path/zone_label.
    return {
        "user_id": user_id,
        "report_signature": signature,
        "report_context": report_context,
    }



def _row_with_optional_columns(
    *,
    user_id: str,
    user_email: str,
    user_name: str = "",
    signature: str,
    report_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Campos diretos/opcionais para persistência forte e compatibilidade.

    No schema atual, estes campos são gravados junto com o ``minimal_row``
    para evitar linhas com colunas diretas vazias em ``client_reports``.
    Em ambientes antigos, a camada de insert adaptativo remove somente
    colunas opcionais que o Supabase informar como inexistentes.
    """
    return {
        "user_id": user_id,
        "user_email": _normalize_text(user_email),
        "title": report_context.get("title") or "Relatório salvo",
        "report_type": report_context.get("report_type") or "urban_report",
        "project_category": report_context.get("project_category") or "",
        "project_option": report_context.get("project_option") or "",
        "zone_code": report_context.get("zone_code") or report_context.get("zone_label") or "",
        "zone_label": report_context.get("zone_label") or report_context.get("zone_code") or "",
        "road_name": report_context.get("road_name") or "",
        "road_type": report_context.get("road_type") or "",
        "lot_area_m2": report_context.get("lot_area_m2") or 0,
        "pdf_bucket": report_context.get("pdf_bucket") or _DEFAULT_BUCKET,
        "pdf_storage_path": report_context.get("pdf_storage_path") or "",
        "pdf_file_name": report_context.get("pdf_file_name") or "relatorio.pdf",
        "pdf_size_bytes": report_context.get("pdf_size_bytes") or 0,
        "file_path": report_context.get("pdf_storage_path") or report_context.get("file_path") or "",
        "status": report_context.get("status") or "saved",
        "report_signature": signature,
        "report_context": report_context,
    }


def _extract_not_null_column(error: Exception) -> str:
    message = str(error)
    patterns = (
        r'null value in column "([^"]+)"',
        r"null value in column '([^']+)'",
    )
    for pattern in patterns:
        match = re.search(pattern, message, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def _extract_unknown_column(error: Exception) -> str:
    message = str(error)
    patterns = (
        r"Could not find the '([^']+)' column",
        r'Could not find the "([^"]+)" column',
        r'column [\w\.]+\."?([A-Za-z_][A-Za-z0-9_]*)"? does not exist',
        r'column "([^"]+)" does not exist',
    )
    for pattern in patterns:
        match = re.search(pattern, message, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def _insert_client_report_schema_compatible(
    client: Client,
    *,
    minimal_row: Dict[str, Any],
    optional_row: Dict[str, Any],
) -> Any:
    """Insere relatório preenchendo colunas diretas quando o schema permitir.

    O banco atual possui colunas diretas úteis para auditoria/listagem
    (title, project_option, zone_code, road_name, pdf_storage_path etc.).
    Por isso começamos com o row completo. Se outro ambiente não tiver alguma
    dessas colunas, removemos apenas a coluna opcional apontada pelo Supabase
    e tentamos de novo. O ``minimal_row`` permanece como piso seguro para
    garantir user_id, report_signature e report_context.
    """
    row = {**minimal_row, **optional_row}
    blocked_columns: set[str] = set()
    protected_columns = {"user_id", "report_signature", "report_context"}
    max_attempts = max(8, len(optional_row) + 3)

    for _ in range(max_attempts):
        try:
            return client.table("client_reports").insert(row).execute()
        except Exception as exc:
            unknown_col = _extract_unknown_column(exc)
            if unknown_col and unknown_col in row and unknown_col not in protected_columns:
                row.pop(unknown_col, None)
                blocked_columns.add(unknown_col)
                continue

            required_col = _extract_not_null_column(exc)
            if (
                required_col
                and required_col in optional_row
                and required_col not in row
                and required_col not in blocked_columns
            ):
                row[required_col] = optional_row[required_col]
                continue

            raise

    return client.table("client_reports").insert(row).execute()




def _normalize_report_row(row: Dict[str, Any]) -> Dict[str, Any]:
    ctx = _ctx(row)
    normalized = dict(row)
    normalized["title"] = row.get("title") or ctx.get("title") or "Relatório salvo"
    calc_snapshot = ctx.get("calc_snapshot") if isinstance(ctx.get("calc_snapshot"), dict) else {}
    session_snapshot = ctx.get("session_snapshot") if isinstance(ctx.get("session_snapshot"), dict) else {}
    normalized["zone_label"] = (
        row.get("zone_label")
        or ctx.get("zone_label")
        or ctx.get("zone_code")
        or ctx.get("zone")
        or _extract_zone(calc_snapshot, session_snapshot)
        or "—"
    )
    normalized["road_name"] = (
        row.get("road_name")
        or ctx.get("road_name")
        or ctx.get("via_nome")
        or ctx.get("street_name")
        or ctx.get("logradouro")
        or _extract_road(calc_snapshot, session_snapshot)
        or "—"
    )
    normalized["pdf_storage_path"] = row.get("pdf_storage_path") or row.get("file_path") or ctx.get("pdf_storage_path") or ctx.get("file_path") or ""
    normalized["pdf_bucket"] = row.get("pdf_bucket") or ctx.get("pdf_bucket") or _DEFAULT_BUCKET
    normalized["pdf_file_name"] = row.get("pdf_file_name") or ctx.get("pdf_file_name") or "relatorio.pdf"
    return normalized


def get_client_report_by_signature(user_id: str, report_signature: str) -> Dict[str, Any] | None:
    """Retorna relatório já salvo para a mesma assinatura, sem tocar em crédito.

    Usado pelo fluxo financeiro antes de debitar para evitar consumo/estorno
    desnecessário quando o usuário volta para um cenário já gerado.
    """
    if not user_id or not report_signature:
        return None

    client = get_supabase_service_client()
    result = (
        client.table("client_reports")
        .select("id,report_signature,report_context")
        .eq("user_id", user_id)
        .eq("report_signature", report_signature)
        .limit(1)
        .execute()
    )
    data = getattr(result, "data", None) or []
    if not data:
        return None
    return _normalize_report_row(data[0])


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

    existing = (
        client.table("client_reports")
        .select("id,report_signature,report_context")
        .eq("user_id", user_id)
        .eq("report_signature", signature)
        .limit(1)
        .execute()
    )
    if existing.data:
        return {"ok": True, "already_exists": True, "row": _normalize_report_row(existing.data[0])}

    storage_path = _storage_path(user_id, signature)
    bucket = _upload_pdf(client, storage_path, pdf_bytes)
    report_context = _report_context(
        calc=calc,
        session_state=session_state,
        user_email=user_email,
        signature=signature,
        storage_path=storage_path,
        user_name=session_state.get("auth_user_name") or session_state.get("auth_name") or "",
        bucket=bucket,
        pdf_bytes=pdf_bytes,
    )
    row = _minimal_row(user_id, signature, report_context)

    try:
        optional_row = _row_with_optional_columns(
            user_id=user_id,
            user_email=user_email,
            signature=signature,
            report_context=report_context,
        )
        inserted = _insert_client_report_schema_compatible(
            client,
            minimal_row=row,
            optional_row=optional_row,
        )
        if inserted.data:
            return {"ok": True, "already_exists": False, "row": _normalize_report_row(inserted.data[0])}

        confirmed = (
            client.table("client_reports")
            .select("id,report_signature,report_context")
            .eq("user_id", user_id)
            .eq("report_signature", signature)
            .limit(1)
            .execute()
        )
        if confirmed.data:
            return {"ok": True, "already_exists": False, "row": _normalize_report_row(confirmed.data[0])}

        raise RuntimeError("Relatório não confirmado no banco após tentativa de inserção.")
    except Exception as exc:
        msg = str(exc).lower()
        if "duplicate key" in msg or "already exists" in msg or "23505" in msg:
            existing = (
                client.table("client_reports")
                .select("id,report_signature,report_context")
                .eq("user_id", user_id)
                .eq("report_signature", signature)
                .limit(1)
                .execute()
            )
            return {
                "ok": True,
                "already_exists": True,
                "row": _normalize_report_row(existing.data[0]) if existing.data else _normalize_report_row(row),
            }
        raise RuntimeError(f"Falha ao registrar relatório no banco: {exc}")


def list_client_reports(user_id: str) -> List[Dict[str, Any]]:
    client = get_supabase_service_client()
    result = (
        client.table("client_reports")
        .select("id,report_signature,report_context,created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [_normalize_report_row(item) for item in (result.data or [])]


def build_download_signed_url(storage_path: str, expires_in: int = 3600, bucket: str | None = None) -> str:
    if not storage_path:
        return ""
    client = get_supabase_service_client()
    buckets = [bucket] if bucket else _configured_buckets()
    for bucket_name in [b for b in buckets if b]:
        try:
            data = client.storage.from_(bucket_name).create_signed_url(storage_path, expires_in)
            if isinstance(data, dict):
                url = data.get("signedURL") or data.get("signedUrl") or ""
                if url:
                    return url
        except Exception:
            continue
    return ""
