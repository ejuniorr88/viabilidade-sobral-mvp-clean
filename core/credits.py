from __future__ import annotations

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


def get_credit_balance(user_id: str) -> int:
    rows = _safe_table_select("credit_balance", filters={"user_id": user_id}, limit=1)
    if not rows:
        return 0
    return int(rows[0].get("balance") or 0)


def list_credit_packages(active_only: bool = True, limit: int = 20) -> List[Dict[str, Any]]:
    filters = {"is_active": True} if active_only else None
    return _safe_table_select(
        "credit_packages",
        filters=filters,
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
