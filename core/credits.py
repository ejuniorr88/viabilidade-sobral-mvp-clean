from __future__ import annotations

import ast
import json
from typing import Any, Dict, List, Optional

from core.auth import get_supabase_auth_client


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
