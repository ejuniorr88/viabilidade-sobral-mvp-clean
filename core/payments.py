from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

import streamlit as st
from supabase import Client, create_client

from core.pix_gateway import MercadoPagoPixError, create_pix_payment, fetch_payment_status


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



def _fetch_payment_row(*, payment_id: str) -> Dict[str, Any]:
    supabase = get_supabase_server_client()
    response = supabase.table("payments").select("*").eq("id", payment_id).limit(1).execute()
    data = _safe_data(response) or []
    if not data:
        raise RuntimeError("Pagamento não encontrado no banco.")
    return data[0]


def _fetch_package_credits(*, package_id: str) -> int:
    supabase = get_supabase_server_client()
    response = supabase.table("credit_packages").select("credits").eq("id", package_id).limit(1).execute()
    data = _safe_data(response) or []
    if not data:
        return 0
    try:
        return int(data[0].get("credits") or 0)
    except Exception:
        return 0


def _payment_already_credited(*, user_id: str, payment_id: str) -> bool:
    supabase = get_supabase_server_client()
    description = f"Crédito por pagamento Pix {payment_id}"
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


def _apply_credit_for_payment(*, payment_row: Dict[str, Any]) -> Dict[str, Any]:
    supabase = get_supabase_server_client()
    user_id = str(payment_row.get("user_id") or "")
    payment_id = str(payment_row.get("id") or "")
    package_id = str(payment_row.get("package_id") or "")
    if not user_id or not payment_id or not package_id:
        return {"credited": False, "reason": "payment_missing_fields"}

    if _payment_already_credited(user_id=user_id, payment_id=payment_id):
        return {"credited": False, "reason": "already_credited"}

    credits = _fetch_package_credits(package_id=package_id)
    if credits <= 0:
        return {"credited": False, "reason": "package_without_credits"}

    balance_resp = supabase.table("credit_balance").select("balance").eq("user_id", user_id).limit(1).execute()
    balance_rows = _safe_data(balance_resp) or []
    current_balance = int((balance_rows[0].get("balance") or 0) if balance_rows else 0)
    new_balance = current_balance + credits

    if balance_rows:
        supabase.table("credit_balance").update({"balance": new_balance}).eq("user_id", user_id).execute()
    else:
        supabase.table("credit_balance").insert({"user_id": user_id, "balance": new_balance}).execute()

    supabase.table("credit_ledger").insert({
        "user_id": user_id,
        "amount": credits,
        "entry_type": "credit",
        "source": "mercadopago_pix",
        "description": f"Crédito por pagamento Pix {payment_id}",
    }).execute()

    return {"credited": True, "credits": credits, "new_balance": new_balance}


def refresh_payment_status_and_credit(*, payment_id: str) -> Dict[str, Any]:
    supabase = get_supabase_server_client()
    payment_row = _fetch_payment_row(payment_id=payment_id)
    external_payment_id = str(payment_row.get("external_payment_id") or "")
    if not external_payment_id:
        return {"ok": False, "message": "Pagamento sem external_payment_id.", "payment": payment_row}

    gateway = fetch_payment_status(external_payment_id)
    mp_status = (gateway.get("status") or "pending").strip().lower()
    normalized_status = "paid" if mp_status == "approved" else mp_status

    update_payload = {
        "status": normalized_status,
        "gateway_payload": gateway.get("gateway_payload") or {},
    }
    response = supabase.table("payments").update(update_payload).eq("id", payment_id).execute()
    data = _safe_data(response) or []
    updated_payment = data[0] if data else {**payment_row, **update_payload}

    credit_result = {"credited": False, "reason": "not_paid"}
    if normalized_status == "paid":
        credit_result = _apply_credit_for_payment(payment_row=updated_payment)

    return {
        "ok": True,
        "message": "Pagamento atualizado.",
        "payment": updated_payment,
        "credit_result": credit_result,
        "gateway_status": mp_status,
    }
