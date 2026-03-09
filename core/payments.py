from __future__ import annotations

from typing import Any, Dict, Optional

from core.auth import get_supabase_auth_client


def create_pending_payment(package_id: str) -> Dict[str, Any]:
    """Cria uma intenção de compra pendente via RPC seguro no Supabase.

    Requer a função SQL public.create_pending_payment(p_package_id uuid).
    """
    supabase = get_supabase_auth_client()
    response = supabase.rpc("create_pending_payment", {"p_package_id": package_id}).execute()

    data = getattr(response, "data", None)
    if data is None and isinstance(response, dict):
        data = response.get("data")

    if isinstance(data, list):
        return data[0] if data else {}
    return data or {}


def get_payment_creation_error(exc: Exception) -> str:
    msg = str(exc)
    if "create_pending_payment" in msg or "Could not find the function" in msg:
        return (
            "A função segura de criação de pagamento ainda não foi criada no Supabase. "
            "Rode primeiro o SQL do arquivo RODE_NO_SUPABASE_create_pending_payment.sql."
        )
    if "violates row-level security" in msg.lower():
        return (
            "O banco bloqueou a criação direta do pagamento. "
            "Use a função segura create_pending_payment no Supabase."
        )
    return msg
