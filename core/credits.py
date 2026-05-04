from __future__ import annotations

import ast
import json
from typing import Any, Dict, List, Optional, Set

import streamlit as st

from core.env_secrets import get_secret, get_secret_str
from supabase import Client, create_client

from core.auth import get_supabase_auth_client


@st.cache_resource(show_spinner=False)
def get_supabase_server_client() -> Client:
    url = get_secret_str("SUPABASE_URL", required=True)
    key = get_secret("SUPABASE_SERVICE_ROLE_KEY")
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


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except Exception:
        return default


def _ledger_row_delta(row: Dict[str, Any]) -> int:
    entry_type = str(row.get("entry_type") or "").strip().lower()
    amount = _to_int(row.get("amount"))

    if entry_type == "credit":
        return amount
    if entry_type == "debit":
        return -amount
    return 0


def _read_credit_balance_value(user_id: str, *, client: Optional[Client] = None) -> int:
    if not user_id:
        return 0

    db = client or get_supabase_server_client()
    rows = _safe_data(db.table("credit_balance").select("balance").eq("user_id", user_id).limit(1).execute()) or []
    if not rows:
        return 0
    return _to_int(rows[0].get("balance"))


def _write_credit_balance_value(user_id: str, balance: int, *, client: Optional[Client] = None) -> None:
    if not user_id:
        return

    db = client or get_supabase_server_client()
    payload = {"user_id": user_id, "balance": int(balance)}

    try:
        db.table("credit_balance").upsert(payload, on_conflict="user_id").execute()
        return
    except Exception:
        pass

    existing = _safe_data(db.table("credit_balance").select("user_id").eq("user_id", user_id).limit(1).execute()) or []
    if existing:
        db.table("credit_balance").update({"balance": int(balance)}).eq("user_id", user_id).execute()
    else:
        db.table("credit_balance").insert(payload).execute()


def _calculate_credit_ledger_balance(user_id: str, *, client: Optional[Client] = None) -> tuple[int, bool]:
    """
    Calcula o saldo pelo histórico de lançamentos.

    Regra consolidada:
    - credit_ledger é a fonte de verdade financeira;
    - credit_balance é apenas saldo materializado/cache.
    """
    if not user_id:
        return 0, False

    db = client or get_supabase_server_client()
    total = 0
    found_any = False
    page_size = 1000
    start = 0

    while True:
        query = (
            db.table("credit_ledger")
            .select("entry_type,amount")
            .eq("user_id", user_id)
            .range(start, start + page_size - 1)
        )
        rows = _safe_data(query.execute()) or []

        for row in rows:
            found_any = True
            total += _ledger_row_delta(row)

        if len(rows) < page_size:
            break

        start += page_size
        if start > 100000:
            # Proteção contra loop infinito em cliente Supabase inesperado.
            break

    return int(total), found_any


def _sync_credit_balance_to_ledger(user_id: str, *, client: Optional[Client] = None) -> Dict[str, Any]:
    """
    Sincroniza o saldo materializado com o ledger quando houver lançamentos.

    Se não houver nenhum lançamento no ledger, preserva o saldo materializado
    para evitar apagar crédito legado sem histórico durante migração.
    """
    if not user_id:
        return {"ok": False, "reason": "missing_user_id", "balance": 0}

    db = client or get_supabase_server_client()
    ledger_balance, ledger_has_rows = _calculate_credit_ledger_balance(user_id, client=db)
    table_balance = _read_credit_balance_value(user_id, client=db)

    if not ledger_has_rows:
        return {
            "ok": True,
            "balance": table_balance,
            "ledger_has_rows": False,
            "table_balance": table_balance,
            "synced": False,
        }

    if table_balance != ledger_balance:
        _write_credit_balance_value(user_id, ledger_balance, client=db)

    return {
        "ok": True,
        "balance": ledger_balance,
        "ledger_has_rows": True,
        "table_balance": table_balance,
        "synced": table_balance != ledger_balance,
    }


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
    """
    Retorna o saldo do usuário com o ledger como fonte de verdade.

    Se houver divergência, corrige credit_balance automaticamente para
    manter a carteira consistente antes de exibir ou validar saldo.
    """
    if not user_id:
        return 0

    try:
        sync = _sync_credit_balance_to_ledger(str(user_id))
        return int(sync.get("balance") or 0)
    except Exception:
        # Fallback conservador: se a sincronização falhar por instabilidade externa,
        # mantém o comportamento antigo para não derrubar a tela.
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
            if parsed.get("ok"):
                try:
                    sync = _sync_credit_balance_to_ledger(user_id)
                    parsed["new_balance"] = sync.get("balance", parsed.get("new_balance"))
                    parsed["balance_source"] = "credit_ledger"
                except Exception:
                    pass
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
    """
    Consolida carteira em caso de troca/duplicidade de user_id para o mesmo e-mail.

    Regra crítica:
    - não somar credit_balance antigo como fonte da verdade;
    - mover o ledger para o usuário atual;
    - recalcular credit_balance a partir do credit_ledger.
    """
    current_user_id = str(current_user_id or "").strip()
    current_email = str(current_email or "").strip().lower()
    if not current_user_id or not current_email:
        return {"ok": False, "reason": "missing_identity"}

    server = get_supabase_server_client()
    candidate_ids: Set[str] = set(_list_auth_user_ids_by_email(current_email))
    candidate_ids.add(current_user_id)

    if len(candidate_ids) <= 1:
        sync = _sync_credit_balance_to_ledger(current_user_id, client=server)
        return {"ok": True, "moved": 0, "balance": int(sync.get("balance") or 0)}

    moved_from: List[str] = []

    for uid in candidate_ids:
        if uid == current_user_id:
            continue

        try:
            server.table("credit_ledger").update({"user_id": current_user_id}).eq("user_id", uid).execute()
        except Exception:
            pass

        try:
            server.table("payments").update({"user_id": current_user_id}).eq("user_id", uid).execute()
        except Exception:
            pass

        try:
            _write_credit_balance_value(uid, 0, client=server)
        except Exception:
            pass

        moved_from.append(uid)

    sync = _sync_credit_balance_to_ledger(current_user_id, client=server)
    final_balance = int(sync.get("balance") or 0)

    return {
        "ok": True,
        "moved": len(moved_from),
        "moved_from": moved_from,
        "balance": final_balance,
        "balance_source": "credit_ledger",
    }


def refund_viability_credit(
    user_id: str,
    amount: int = 1,
    description: str = "Estorno de crédito de viabilidade",
    *,
    reference_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Compensa um débito anterior mantendo o credit_ledger como fonte de verdade.

    Proteção crítica:
    - quando houver reference_id, usa idempotency_key estável para evitar
      estorno duplicado em caso de retry/rerun;
    - source = refund_process para auditoria clara do tipo de lançamento.
    """
    if not user_id:
        return {"ok": False, "message": "Usuário não identificado para estorno."}

    server = get_supabase_server_client()
    reference_key = str(reference_id or "").strip()
    idempotency_key = f"refund_viability_credit:{user_id}:{reference_key}:{int(amount)}" if reference_key else None

    try:
        if idempotency_key:
            existing_refund = _safe_data(
                server.table("credit_ledger")
                .select("id")
                .eq("user_id", user_id)
                .eq("idempotency_key", idempotency_key)
                .limit(1)
                .execute()
            ) or []
            if existing_refund:
                sync = _sync_credit_balance_to_ledger(user_id, client=server)
                return {
                    "ok": True,
                    "already_refunded": True,
                    "new_balance": int(sync.get("balance") or 0),
                    "amount": int(amount),
                    "balance_source": "credit_ledger",
                }

        ledger_payload = {
            "user_id": user_id,
            "amount": int(amount),
            "entry_type": "credit",
            "source": "refund_process",
            "description": description,
            "metadata": metadata or {},
        }
        if reference_key:
            ledger_payload["reference_id"] = reference_key
        if idempotency_key:
            ledger_payload["idempotency_key"] = idempotency_key

        server.table("credit_ledger").insert(ledger_payload).execute()
        sync = _sync_credit_balance_to_ledger(user_id, client=server)
        new_balance = int(sync.get("balance") or 0)
        return {
            "ok": True,
            "already_refunded": False,
            "new_balance": new_balance,
            "amount": int(amount),
            "balance_source": "credit_ledger",
        }
    except Exception as e:
        return {"ok": False, "message": f"Erro ao estornar crédito: {e}"}
