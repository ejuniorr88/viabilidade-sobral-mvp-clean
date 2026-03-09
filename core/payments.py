from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

import streamlit as st
from supabase import Client, create_client

from core.pix_gateway import MercadoPagoPixError, create_pix_payment


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
