from __future__ import annotations

import ast
import json
from typing import Any, Dict, List, Optional, Set

import streamlit as st
from supabase import Client, create_client

from core.auth import get_supabase_auth_client


@st.cache_resource(show_spinner=False)
def get_supabase_server_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY")
    if not key:
        raise RuntimeError("Falta configurar SUPABASE_SERVICE_ROLE_KEY nos Secrets do Streamlit.")
    return create_client(url, key)


def _safe_data(response: Any) -> Any:
    data = getattr(response, "data", None)
    if data is None and isinstance(response, dict):
        data = response.get("data")
    return data


def _safe_table_select(
    table_name: str,
    *,
    filters: Optional[Dict[str, Any]] = None,
    order_by: Optional[str] = None,
    desc: bool = False,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    supabase = get_supabase_auth_client()
    query = supabase.table(table_name).select("*")

    if filters:
        for key, value in filters.items():
            query = query.eq(key, value)

    if order_by:
        query = query.order(order_by, desc=desc)

    if limit:
        query = query.limit(limit)

    response = query.execute()
    data = getattr(response, "data", None)
    if data is None and isinstance(response, dict):
        data = response.get("data")
    return data or []


def _parse_rpc_payload(value: Any) -> Optional[Dict[str, Any]]:
    """
    Normaliza respostas de RPC que podem vir como:
    - dict
    - JSON string
    - bytes
    - string representando bytes: b'{"ok": true, ...}'
    """
    if value is None:
        return None

    if isinstance(value, dict):
        return value

    if isinstance(value, bytes):
        try:
            return json.loads(value.decode("utf-8"))
        except Exception:
            return None

    if isinstance(value, str):
        s = value.strip()

        # Caso venha como string normal JSON
        if s.startswith("{") and s.endswith("}"):
            try:
                return json.loads(s)
            except Exception:
                pass

        # Caso venha como representação textual de bytes: b'...'
        if s.startswith("b'") or s.startswith('b"'):
            try:
                raw_bytes = ast.literal_eval(s)
                if isinstance(raw_bytes, bytes):
                    return json.loads(raw_bytes.decode("utf-8"))
            except Exception:
                pass

    return None


def _extract_rpc_json(response: Any) -> Optional[Dict[str, Any]]:
    # Caso comum
    data = getattr(response, "data", None)
    parsed = _parse_rpc_payload(data)
    if parsed is not None:
        return parsed

    # Caso response já seja dict
    if isinstance(response, dict):
        parsed = _parse_rpc_payload(response.get("data"))
        if parsed is not None:
            return parsed

        # Às vezes já vem no próprio dict
        parsed = _parse_rpc_payload(response)
        if parsed is not None:
            return parsed

        # Alguns clientes colocam o erro em message/details
        details = response.get("details")
        parsed = _parse_rpc_payload(details)
        if parsed is not None:
            return parsed

        message = response.get("message")
        parsed = _parse_rpc_payload(message)
        if parsed is not None:
            return parsed

    # Caso o client lance objeto com details/message
    details = getattr(response, "details", None)
    parsed = _parse_rpc_payload(details)
    if parsed is not None:
        return parsed

    message = getattr(response, "message", None)
    parsed = _parse_rpc_payload(message)
    if parsed is not None:
        return parsed

    return None


def get_credit_balance(user_id: str) -> int:
    rows = _safe_table_select("credit_balance", filters={"user_id": user_id}, limit=1)
    if not rows:
        return 0
    return int(rows[0].get("balance") or 0)


def list_credit_packages(active_only: bool = True, limit: int = 20) -> List[Dict[str, Any]]:
    supabase = get_supabase_auth_client()

    if active_only:
        try:
            response = (
                supabase.table("credit_packages")
                .select("*")
                .eq("is_active", True)
                .order("price_brl", desc=False)
                .limit(limit)
                .execute()
            )
            data = getattr(response, "data", None)
            if data:
                return data
        except Exception:
            pass

        try:
            response = (
                supabase.table("credit_packages")
                .select("*")
                .eq("active", True)
                .order("price_brl", desc=False)
                .limit(limit)
                .execute()
            )
            data = getattr(response, "data", None)
            return data or []
        except Exception:
            return []

    return _safe_table_select(
        "credit_packages",
        filters=None,
        order_by="price_brl",
        desc=False,
        limit=limit,
    )


def list_credit_ledger(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    return _safe_table_select(
        "credit_ledger",
        filters={"user_id": user_id},
        order_by="created_at",
        desc=True,
        limit=limit,
    )


def list_user_payments(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    return _safe_table_select(
        "payments",
        filters={"user_id": user_id},
        order_by="created_at",
        desc=True,
        limit=limit,
    )


def consume_viability_credit(
    user_id: str,
    amount: int = 1,
    description: str = "Cálculo de viabilidade",
) -> Dict[str, Any]:
    supabase = get_supabase_auth_client()

    try:
        response = supabase.rpc(
            "consume_viability_credit",
            {
                "p_user_id": user_id,
                "p_amount": amount,
                "p_description": description,
            },
        ).execute()

        parsed = _extract_rpc_json(response)
        if parsed is not None:
            return parsed

        return {
            "ok": False,
            "message": "Não foi possível interpretar a resposta do consumo de crédito.",
            "raw_response": str(response),
        }

    except Exception as e:
        parsed = _extract_rpc_json(e)
        if parsed is not None:
            return parsed

        return {
            "ok": False,
            "message": f"Erro ao consumir crédito: {e}",
        }


def _list_auth_user_ids_by_email(email: Optional[str]) -> List[str]:
    if not email:
        return []
    try:
        admin = get_supabase_server_client().auth.admin
        response = admin.list_users()
        users = getattr(response, "users", None)
        if users is None and isinstance(response, dict):
            users = response.get("users")
        result: List[str] = []
        for user in users or []:
            user_email = getattr(user, "email", None)
            user_id = getattr(user, "id", None)
            if user_email and user_id and str(user_email).strip().lower() == str(email).strip().lower():
                result.append(str(user_id))
        return result
    except Exception:
        return []


def reconcile_wallet_to_current_user(current_user_id: Optional[str], current_email: Optional[str]) -> Dict[str, Any]:
    current_user_id = str(current_user_id or "").strip()
    current_email = str(current_email or "").strip().lower()
    if not current_user_id or not current_email:
        return {"ok": False, "reason": "missing_identity"}

    server = get_supabase_server_client()
    candidate_ids: Set[str] = set(_list_auth_user_ids_by_email(current_email))
    candidate_ids.add(current_user_id)

    if len(candidate_ids) <= 1:
        return {"ok": True, "moved": 0, "balance": get_credit_balance(current_user_id)}

    moved_from: List[str] = []
    total_balance = 0
    for uid in candidate_ids:
        rows = _safe_data(server.table("credit_balance").select("balance").eq("user_id", uid).limit(1).execute()) or []
        bal = int((rows[0].get("balance") or 0) if rows else 0)
        total_balance += bal
        if uid != current_user_id:
            try:
                server.table("credit_ledger").update({"user_id": current_user_id}).eq("user_id", uid).execute()
            except Exception:
                pass
            try:
                server.table("payments").update({"user_id": current_user_id}).eq("user_id", uid).execute()
            except Exception:
                pass
            try:
                server.table("credit_balance").upsert({"user_id": uid, "balance": 0}, on_conflict="user_id").execute()
            except Exception:
                try:
                    existing = _safe_data(server.table("credit_balance").select("user_id").eq("user_id", uid).limit(1).execute()) or []
                    if existing:
                        server.table("credit_balance").update({"balance": 0}).eq("user_id", uid).execute()
                    else:
                        server.table("credit_balance").insert({"user_id": uid, "balance": 0}).execute()
                except Exception:
                    pass
            moved_from.append(uid)

    try:
        server.table("credit_balance").upsert({"user_id": current_user_id, "balance": total_balance}, on_conflict="user_id").execute()
    except Exception:
        existing = _safe_data(server.table("credit_balance").select("user_id").eq("user_id", current_user_id).limit(1).execute()) or []
        if existing:
            server.table("credit_balance").update({"balance": total_balance}).eq("user_id", current_user_id).execute()
        else:
            server.table("credit_balance").insert({"user_id": current_user_id, "balance": total_balance}).execute()

    return {
        "ok": True,
        "moved": len(moved_from),
        "moved_from": moved_from,
        "balance": total_balance,
    }


def refund_viability_credit(
    user_id: str,
    amount: int = 1,
    description: str = "Estorno de crédito de viabilidade",
    *,
    reference_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compensa um débito anterior de crédito quando a persistência do relatório falha."""
    if not user_id:
        return {"ok": False, "message": "Usuário não identificado para estorno."}

    server = get_supabase_server_client()
    current_balance = get_credit_balance(user_id)
    new_balance = int(current_balance) + int(amount)

    try:
        existing = _safe_data(server.table("credit_balance").select("user_id").eq("user_id", user_id).limit(1).execute()) or []
        if existing:
            server.table("credit_balance").update({"balance": new_balance}).eq("user_id", user_id).execute()
        else:
            server.table("credit_balance").insert({"user_id": user_id, "balance": new_balance}).execute()

        ledger_payload = {
            "user_id": user_id,
            "amount": int(amount),
            "entry_type": "credit",
            "source": "platform_usage",
            "reference_id": reference_id or "report_storage_refund",
            "description": description,
            "metadata": metadata or {},
        }
        try:
            server.table("credit_ledger").insert(ledger_payload).execute()
        except Exception:
            pass

        return {"ok": True, "new_balance": new_balance, "amount": int(amount)}
    except Exception as e:
        return {"ok": False, "message": f"Erro ao estornar crédito: {e}"}
