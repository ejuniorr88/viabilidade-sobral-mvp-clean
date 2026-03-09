from __future__ import annotations

from typing import Any, Dict
from uuid import uuid4

import streamlit as st
from supabase import Client, create_client

from core.auth import get_supabase_auth_client


@st.cache_resource(show_spinner=False)
def get_supabase_service_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


def _extract_response_data(response: Any) -> Any:
    data = getattr(response, "data", None)
    if data is None and isinstance(response, dict):
        data = response.get("data")
    return data


def create_pending_payment(package_id: str, user_id: str) -> Dict[str, Any]:
    """Cria uma intenção de compra pendente usando client server-side.

    Usa a service role no servidor do Streamlit para não depender do contexto
    auth.uid() na RPC. O user_id vem do usuário já autenticado no app.
    """
    if not user_id:
        raise ValueError("Usuário não autenticado no app.")

    service = get_supabase_service_client()

    pkg_response = (
        service.table("credit_packages")
        .select("id,name,description,price_brl,credits,is_active")
        .eq("id", package_id)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    pkg_data = _extract_response_data(pkg_response) or []
    if not pkg_data:
        raise ValueError("Pacote não encontrado ou inativo.")

    package = pkg_data[0]
    external_reference = f"pkg_{str(user_id).replace('-', '')}_{uuid4().hex}"

    insert_payload = {
        "user_id": user_id,
        "package_id": package_id,
        "gateway": "pending_internal",
        "external_reference": external_reference,
        "amount_brl": package.get("price_brl"),
        "status": "pending",
    }

    payment_response = service.table("payments").insert(insert_payload).execute()
    payment_data = _extract_response_data(payment_response)

    if isinstance(payment_data, list):
        return payment_data[0] if payment_data else {}
    return payment_data or {}



def get_payment_creation_error(exc: Exception) -> str:
    msg = str(exc)
    lowered = msg.lower()

    if "supabase_service_role_key" in lowered:
        return (
            "Falta configurar SUPABASE_SERVICE_ROLE_KEY nos Secrets do Streamlit. "
            "Sem essa chave o app não consegue criar a compra pendente com segurança."
        )
    if "usuário não autenticado" in lowered or "user_id" in lowered:
        return "Usuário não autenticado. Faça login novamente com Google e tente de novo."
    if "duplicate key" in lowered or "external_reference" in lowered:
        return "Houve um conflito ao gerar a referência da compra. Tente novamente."
    if "row-level security" in lowered:
        return "O banco bloqueou a operação. Verifique as permissões da tabela payments."
    return msg
