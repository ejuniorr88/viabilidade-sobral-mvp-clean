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
    coupon_applied: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    supabase = get_supabase_server_client()
    original_amount = float((coupon_applied or {}).get("original_amount") or package.get("price_brl") or 0)
    discount_amount = float((coupon_applied or {}).get("discount_amount") or 0)
    final_amount = float((coupon_applied or {}).get("final_amount") or original_amount)
    payload = {
        "user_id": user_id,
        "package_id": package["id"],
        "gateway": "mercadopago_pix_test",
        "external_reference": _generate_external_reference(user_id),
        "amount_brl": final_amount,
        "status": "pending",
        "coupon_id": (coupon_applied or {}).get("coupon_id"),
        "coupon_code": (coupon_applied or {}).get("coupon_code"),
        "coupon_owner_user_id": (coupon_applied or {}).get("coupon_owner_user_id"),
        "discount_type": (coupon_applied or {}).get("discount_type"),
        "discount_value": (coupon_applied or {}).get("discount_value"),
        "original_amount": original_amount,
        "discount_amount": discount_amount,
        "final_amount": final_amount,
        "coupon_snapshot": (coupon_applied or {}).get("snapshot"),
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
    coupon_applied: Optional[Dict[str, Any]] = None,
    notification_url: Optional[str] = None,
) -> Dict[str, Any]:
    pending = create_pending_payment_server_side(user_id=user_id, package=package, coupon_applied=coupon_applied)

    try:
        amount_for_pix = float((coupon_applied or {}).get("final_amount") or package.get("price_brl") or 0)
        pix = create_pix_payment(
            amount_brl=amount_for_pix,
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


def _get_payment_credit_row(*, payment_id: str) -> Optional[Dict[str, Any]]:
    supabase = get_supabase_server_client()
    description = f"Crédito por pagamento Pix {payment_id}"
    response = (
        supabase.table("credit_ledger")
        .select("*")
        .eq("source", "pix_purchase")
        .eq("description", description)
        .limit(1)
        .execute()
    )
    data = _safe_data(response) or []
    return data[0] if data else None


def _coerce_coupon_usage_payment_id(payment_id: Any) -> Optional[int]:
    try:
        if payment_id is None or payment_id == "":
            return None
        return int(payment_id)
    except Exception:
        return None


def _get_coupon_usage_row_for_payment(*, payment_row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    supabase = get_supabase_server_client()
    payment_id = _coerce_coupon_usage_payment_id(payment_row.get("id"))
    external_reference = str(payment_row.get("external_reference") or "")

    query = supabase.table("coupon_usages").select("*")
    if payment_id is not None:
        response = query.eq("payment_id", payment_id).limit(1).execute()
        data = _safe_data(response) or []
        if data:
            return data[0]

    if external_reference:
        response = (
            supabase.table("coupon_usages")
            .select("*")
            .eq("payment_external_reference", external_reference)
            .limit(1)
            .execute()
        )
        data = _safe_data(response) or []
        if data:
            return data[0]

    return None


def _record_coupon_usage_for_paid_payment(*, payment_row: Dict[str, Any]) -> Dict[str, Any]:
    supabase = get_supabase_server_client()
    coupon_id = payment_row.get("coupon_id")
    coupon_code = str(payment_row.get("coupon_code") or "").strip()
    if not coupon_id or not coupon_code:
        return {"recorded": False, "reason": "no_coupon"}

    existing = _get_coupon_usage_row_for_payment(payment_row=payment_row)
    if existing:
        return {"recorded": False, "reason": "already_recorded", "usage": existing}

    original_amount = float(payment_row.get("original_amount") or payment_row.get("amount_brl") or 0)
    discount_amount = float(payment_row.get("discount_amount") or 0)
    final_amount = float(payment_row.get("final_amount") or payment_row.get("amount_brl") or original_amount)
    payload = {
        "coupon_id": coupon_id,
        "coupon_code": coupon_code,
        "owner_user_id": payment_row.get("coupon_owner_user_id"),
        "used_by_user_id": payment_row.get("user_id"),
        "used_by_email": ((payment_row.get("coupon_snapshot") or {}).get("used_by_email") if isinstance(payment_row.get("coupon_snapshot"), dict) else None),
        "payment_id": _coerce_coupon_usage_payment_id(payment_row.get("id")),
        "payment_external_reference": payment_row.get("external_reference"),
        "plan_code": str(payment_row.get("package_id") or ""),
        "original_amount": original_amount,
        "discount_amount": discount_amount,
        "final_amount": final_amount,
        "payment_status": str(payment_row.get("status") or "paid"),
        "confirmed_at": "now()",
    }
    response = supabase.table("coupon_usages").insert(payload).execute()
    data = _safe_data(response) or []
    return {"recorded": True, "usage": (data[0] if data else payload)}


def _read_balance(*, user_id: str) -> int:
    supabase = get_supabase_server_client()
    balance_resp = supabase.table("credit_balance").select("balance").eq("user_id", user_id).limit(1).execute()
    balance_rows = _safe_data(balance_resp) or []
    return int((balance_rows[0].get("balance") or 0) if balance_rows else 0)


def _write_balance(*, user_id: str, balance: int) -> None:
    supabase = get_supabase_server_client()
    balance_resp = supabase.table("credit_balance").select("balance").eq("user_id", user_id).limit(1).execute()
    balance_rows = _safe_data(balance_resp) or []
    if balance_rows:
        supabase.table("credit_balance").update({"balance": balance}).eq("user_id", user_id).execute()
    else:
        supabase.table("credit_balance").insert({"user_id": user_id, "balance": balance}).execute()


def _move_credit_to_user(*, payment_row: Dict[str, Any], credit_row: Dict[str, Any], target_user_id: str) -> Dict[str, Any]:
    supabase = get_supabase_server_client()
    old_user_id = str(credit_row.get("user_id") or "")
    payment_id = str(payment_row.get("id") or "")
    credits = int(credit_row.get("amount") or 0)
    if not old_user_id or not target_user_id or credits <= 0:
        return {"credited": False, "reason": "move_missing_fields"}
    if old_user_id == target_user_id:
        return {"credited": False, "reason": "already_credited"}

    old_balance = _read_balance(user_id=old_user_id)
    target_balance = _read_balance(user_id=target_user_id)
    _write_balance(user_id=old_user_id, balance=max(0, old_balance - credits))
    _write_balance(user_id=target_user_id, balance=target_balance + credits)

    supabase.table("credit_ledger").update({"user_id": target_user_id}).eq("id", credit_row.get("id")).execute()
    supabase.table("payments").update({"user_id": target_user_id}).eq("id", payment_id).execute()
    return {"credited": True, "credits": credits, "new_balance": target_balance + credits, "moved": True}


def _apply_credit_for_payment(*, payment_row: Dict[str, Any], target_user_id: Optional[str] = None) -> Dict[str, Any]:
    supabase = get_supabase_server_client()
    payment_user_id = str(payment_row.get("user_id") or "")
    user_id = str(target_user_id or payment_user_id or "")
    payment_id = str(payment_row.get("id") or "")
    package_id = str(payment_row.get("package_id") or "")
    if not user_id or not payment_id or not package_id:
        return {"credited": False, "reason": "payment_missing_fields"}

    existing_credit = _get_payment_credit_row(payment_id=payment_id)
    if existing_credit:
        existing_user_id = str(existing_credit.get("user_id") or "")
        if existing_user_id == user_id:
            return {"credited": False, "reason": "already_credited"}
        return _move_credit_to_user(payment_row=payment_row, credit_row=existing_credit, target_user_id=user_id)

    credits = _fetch_package_credits(package_id=package_id)
    if credits <= 0:
        return {"credited": False, "reason": "package_without_credits"}

    current_balance = _read_balance(user_id=user_id)
    new_balance = current_balance + credits
    _write_balance(user_id=user_id, balance=new_balance)

    supabase.table("credit_ledger").insert({
        "user_id": user_id,
        "amount": credits,
        "entry_type": "credit",
        "source": "pix_purchase",
        "description": f"Crédito por pagamento Pix {payment_id}",
    }).execute()
    if payment_user_id != user_id:
        supabase.table("payments").update({"user_id": user_id}).eq("id", payment_id).execute()

    return {"credited": True, "credits": credits, "new_balance": new_balance}


def ensure_paid_payment_is_credited(*, payment_id: str, target_user_id: Optional[str] = None) -> Dict[str, Any]:
    """Reprocessa um pagamento já marcado como paid para garantir crédito na carteira."""
    payment_row = _fetch_payment_row(payment_id=payment_id)
    status = str(payment_row.get("status") or "").strip().lower()
    if status != "paid":
        return {"ok": False, "message": "Pagamento ainda não está pago.", "payment": payment_row}

    credit_result = _apply_credit_for_payment(payment_row=payment_row, target_user_id=target_user_id)
    coupon_result = _record_coupon_usage_for_paid_payment(payment_row=payment_row)
    return {
        "ok": True,
        "message": "Pagamento reprocessado para crédito.",
        "payment": payment_row,
        "credit_result": credit_result,
        "coupon_result": coupon_result,
    }

def refresh_payment_status_and_credit(*, payment_id: str, target_user_id: Optional[str] = None) -> Dict[str, Any]:
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
    coupon_result = {"recorded": False, "reason": "not_paid"}
    if normalized_status == "paid":
        credit_result = _apply_credit_for_payment(payment_row=updated_payment, target_user_id=target_user_id)
        coupon_result = _record_coupon_usage_for_paid_payment(payment_row=updated_payment)

    return {
        "ok": True,
        "message": "Pagamento atualizado.",
        "payment": updated_payment,
        "credit_result": credit_result,
        "coupon_result": coupon_result,
        "gateway_status": mp_status,
    }
