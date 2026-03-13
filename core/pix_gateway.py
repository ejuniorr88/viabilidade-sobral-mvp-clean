from __future__ import annotations

import base64
import uuid
from typing import Any, Dict, Optional

import requests
import streamlit as st

MERCADOPAGO_API_BASE = "https://api.mercadopago.com"


class MercadoPagoPixError(Exception):
    pass


def _split_name(full_name: str) -> tuple[str, str]:
    parts = [p for p in (full_name or "").strip().split() if p]
    if not parts:
        return "Comprador", "Teste"
    if len(parts) == 1:
        return parts[0], "Teste"
    return parts[0], " ".join(parts[1:])


def _build_payer(email: str, full_name: str) -> Dict[str, Any]:
    first_name, last_name = _split_name(full_name)
    return {
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
    }


def _get_access_token() -> str:
    token = st.secrets.get("MERCADOPAGO_ACCESS_TOKEN")
    if not token:
        raise MercadoPagoPixError(
            "Falta configurar MERCADOPAGO_ACCESS_TOKEN nos Secrets do Streamlit."
        )
    return str(token)


def create_pix_payment(
    *,
    amount_brl: float,
    description: str,
    payer_email: str,
    payer_name: str,
    external_reference: str,
    notification_url: Optional[str] = None,
) -> Dict[str, Any]:
    access_token = _get_access_token()

    payload: Dict[str, Any] = {
        "transaction_amount": round(float(amount_brl), 2),
        "description": description,
        "payment_method_id": "pix",
        "payer": _build_payer(payer_email, payer_name),
        "external_reference": external_reference,
    }

    if notification_url:
        payload["notification_url"] = notification_url

    response = requests.post(
        f"{MERCADOPAGO_API_BASE}/v1/payments",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Idempotency-Key": str(uuid.uuid4()),
        },
        json=payload,
        timeout=45,
    )

    if response.status_code >= 400:
        raise MercadoPagoPixError(
            f"Mercado Pago retornou erro {response.status_code}: {response.text}"
        )

    data = response.json()
    poi = data.get("point_of_interaction") or {}
    tx = poi.get("transaction_data") or {}

    return {
        "external_payment_id": str(data.get("id") or ""),
        "status": data.get("status") or "pending",
        "status_detail": data.get("status_detail"),
        "ticket_url": tx.get("ticket_url"),
        "qr_code": tx.get("qr_code"),
        "qr_code_base64": tx.get("qr_code_base64"),
        "gateway_payload": data,
    }


def qr_code_image_data_uri(qr_code_base64: Optional[str]) -> Optional[str]:
    if not qr_code_base64:
        return None
    try:
        base64.b64decode(qr_code_base64)
        return f"data:image/png;base64,{qr_code_base64}"
    except Exception:
        return None


def get_payment_status(external_payment_id: str) -> Dict[str, Any]:
    access_token = _get_access_token()
    payment_id = str(external_payment_id or '').strip()
    if not payment_id:
        raise MercadoPagoPixError('external_payment_id ausente para consulta do pagamento.')

    response = requests.get(
        f"{MERCADOPAGO_API_BASE}/v1/payments/{payment_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        timeout=45,
    )

    if response.status_code >= 400:
        raise MercadoPagoPixError(
            f"Mercado Pago retornou erro {response.status_code} ao consultar pagamento: {response.text}"
        )

    data = response.json()
    return {
        "external_payment_id": str(data.get("id") or payment_id),
        "status": data.get("status") or "pending",
        "status_detail": data.get("status_detail"),
        "date_approved": data.get("date_approved"),
        "gateway_payload": data,
    }
