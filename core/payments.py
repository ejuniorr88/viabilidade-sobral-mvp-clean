from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

import streamlit as st
from supabase import Client, create_client

from core.pix_gateway import MercadoPagoPixError, create_pix_payment, get_payment_status


@st.cache_resource(show_spinner=False)
def get_supabase_server_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY")
    if not key:
        raise RuntimeError(
            "Falta configurar SUPABASE_SERVICE_ROLE_KEY nos Secrets do Streamlit."
        )
    return create_client(url, key)


def _safe_data(response: Any) -> Any:
    data = getattr(response, "data", None)
    if data is None and isinstance(response, dict):
        data = response.get("data")
    return data


def _generate_external_reference(user_id: str) -> str:
    return f"pkg_{user_id.replace('-', '')}_{uuid.uuid4().hex}"


def create_pending_payment_server_side(
    *,
    user_id: str,
    package: Dict[str, Any],
) -> Dict[str, Any]:
    supabase = get_supabase_server_client()
    payload = {
        "user_id": user_id,
        "package_id": package["id"],
        "gateway": "mercadopago_pix_test",
        "external_reference": _generate_external_reference(user_id),
        "amount_brl": float(package.get("price_brl") or 0),
        "status": "pending",
    }
    response = supabase.table("payments").insert(payload).execute()
    data = _safe_data(response) or []
    if not data:
        raise RuntimeError("Não foi possível criar o pagamento pendente no banco.")
    return data[0]


def update_payment_with_pix_data(
    *,
    payment_id: str,
    external_payment_id: str,
    pix_qr_code: Optional[str],
    pix_qr_code_base64: Optional[str],
    ticket_url: Optional[str],
    gateway_payload: Dict[str, Any],
) -> Dict[str, Any]:
    supabase = get_supabase_server_client()
    update_payload = {
        "external_payment_id": external_payment_id,
        "pix_copy_paste": pix_qr_code,
        "pix_qr_code": pix_qr_code_base64,
        "gateway_payload": {
            **(gateway_payload or {}),
            "ticket_url": ticket_url,
        },
        "updated_at": "now()",
    }
    response = (
        supabase.table("payments")
        .update(update_payload)
        .eq("id", payment_id)
        .execute()
    )
    data = _safe_data(response) or []
    return data[0] if data else update_payload


def create_pending_payment_and_pix(
    *,
    user_id: str,
    user_email: str,
    user_name: str,
    package: Dict[str, Any],
    notification_url: Optional[str] = None,
) -> Dict[str, Any]:
    pending = create_pending_payment_server_side(user_id=user_id, package=package)

    try:
        pix = create_pix_payment(
            amount_brl=float(package.get("price_brl") or 0),
            description=f"{package.get('name') or 'Pacote de créditos'}",
            payer_email=user_email,
            payer_name=user_name or user_email,
            external_reference=pending["external_reference"],
            notification_url=notification_url,
        )
    except MercadoPagoPixError:
        raise
    except Exception as e:
        raise RuntimeError(f"Erro inesperado ao gerar Pix no Mercado Pago: {e}") from e

    updated = update_payment_with_pix_data(
        payment_id=pending["id"],
        external_payment_id=pix.get("external_payment_id") or "",
        pix_qr_code=pix.get("qr_code"),
        pix_qr_code_base64=pix.get("qr_code_base64"),
        ticket_url=pix.get("ticket_url"),
        gateway_payload=pix.get("gateway_payload") or {},
    )

    return {
        "pending": pending,
        "updated": updated,
        "pix": pix,
    }


def _fetch_payment_server_side(payment_id: str) -> Optional[Dict[str, Any]]:
    supabase = get_supabase_server_client()
    response = (
        supabase.table("payments")
        .select("*")
        .eq("id", payment_id)
        .limit(1)
        .execute()
    )
    data = _safe_data(response) or []
    return data[0] if data else None


def _fetch_package_server_side(package_id: str) -> Optional[Dict[str, Any]]:
    supabase = get_supabase_server_client()
    response = (
        supabase.table("credit_packages")
        .select("*")
        .eq("id", package_id)
        .limit(1)
        .execute()
    )
    data = _safe_data(response) or []
    return data[0] if data else None


def _credits_already_applied(user_id: str, payment_id: str) -> bool:
    supabase = get_supabase_server_client()
    description = f"Créditos adicionados via Pix ({payment_id})"
    response = (
        supabase.table("credit_ledger")
        .select("id")
        .eq("user_id", user_id)
        .eq("source", "mercadopago_pix")
        .eq("description", description)
        .limit(1)
        .execute()
    )
    data = _safe_data(response) or []
    return bool(data)


def _apply_credits_for_paid_payment(payment_row: Dict[str, Any]) -> Dict[str, Any]:
    supabase = get_supabase_server_client()
    user_id = str(payment_row.get("user_id") or "").strip()
    package_id = str(payment_row.get("package_id") or "").strip()
    payment_id = str(payment_row.get("id") or "").strip()

    if not user_id or not package_id or not payment_id:
        raise RuntimeError("Pagamento sem user_id/package_id/id suficientes para creditar carteira.")

    if _credits_already_applied(user_id, payment_id):
        return {"ok": True, "already_applied": True, "credits": 0}

    package = _fetch_package_server_side(package_id)
    if not package:
        raise RuntimeError("Pacote de créditos não encontrado para o pagamento aprovado.")

    credits = int(float(package.get("credits") or 0))
    if credits <= 0:
        raise RuntimeError("Pacote com quantidade de créditos inválida.")

    current_resp = (
        supabase.table("credit_balance")
        .select("balance")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    current_rows = _safe_data(current_resp) or []
    current_balance = int(float((current_rows[0].get("balance") if current_rows else 0) or 0))
    new_balance = current_balance + credits

    if current_rows:
        supabase.table("credit_balance").update({"balance": new_balance}).eq("user_id", user_id).execute()
    else:
        supabase.table("credit_balance").insert({"user_id": user_id, "balance": new_balance}).execute()

    supabase.table("credit_ledger").insert({
        "user_id": user_id,
        "entry_type": "credit",
        "amount": credits,
        "source": "mercadopago_pix",
        "description": f"Créditos adicionados via Pix ({payment_id})",
    }).execute()

    return {"ok": True, "already_applied": False, "credits": credits, "new_balance": new_balance}


def sync_payment_status_and_apply_credits(payment_id: str) -> Dict[str, Any]:
    payment_row = _fetch_payment_server_side(payment_id)
    if not payment_row:
        raise RuntimeError("Pagamento não encontrado no banco para sincronização.")

    external_payment_id = str(payment_row.get("external_payment_id") or "").strip()
    if not external_payment_id:
        raise RuntimeError("Pagamento sem external_payment_id para consultar no Mercado Pago.")

    mp_data = get_payment_status(external_payment_id)
    new_status = (mp_data.get("status") or "pending").lower()

    supabase = get_supabase_server_client()
    gateway_payload = payment_row.get("gateway_payload") or {}
    if not isinstance(gateway_payload, dict):
        gateway_payload = {"previous_payload": gateway_payload}
    merged_payload = {**gateway_payload, "status_sync": mp_data}

    update_payload = {
        "status": new_status,
        "gateway_payload": merged_payload,
    }
    detail = mp_data.get("status_detail")
    if detail and "status_detail" in payment_row:
        update_payload["status_detail"] = detail

    try:
        update_payload["updated_at"] = "now()"
    except Exception:
        pass

    supabase.table("payments").update(update_payload).eq("id", payment_id).execute()

    credits_result = {"ok": False, "already_applied": False, "credits": 0}
    if new_status in ("approved", "paid"):
        credits_result = _apply_credits_for_paid_payment({**payment_row, **update_payload})
        if new_status == "approved":
            supabase.table("payments").update({"status": "paid"}).eq("id", payment_id).execute()
            new_status = "paid"

    refreshed = _fetch_payment_server_side(payment_id) or {**payment_row, **update_payload, "status": new_status}
    return {
        "payment": refreshed,
        "status": new_status,
        "status_detail": detail,
        "credits": credits_result,
        "gateway": mp_data,
    }
