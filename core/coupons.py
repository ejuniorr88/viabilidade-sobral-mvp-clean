from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import streamlit as st
from supabase import Client, create_client


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


def _normalize_coupon_code(value: Any) -> str:
    return str(value or "").strip().upper()


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        s = str(value).strip()
        if not s:
            return None
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(s)
        except Exception:
            return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _resolve_plan_code(package: Dict[str, Any]) -> str:
    return str(package.get("code") or package.get("slug") or package.get("id") or "").strip()


def _load_coupon_by_code(code: str) -> Optional[Dict[str, Any]]:
    normalized = _normalize_coupon_code(code)
    if not normalized:
        return None
    supabase = get_supabase_server_client()
    response = supabase.table("coupon_codes").select("*").execute()
    rows = _safe_data(response) or []
    for row in rows:
        if _normalize_coupon_code(row.get("code")) == normalized:
            return row
    return None


def _count_coupon_usages(*, coupon_id: Any, used_by_user_id: Optional[str] = None) -> int:
    supabase = get_supabase_server_client()
    response = supabase.table("coupon_usages").select("*").eq("coupon_id", coupon_id).execute()
    rows: List[Dict[str, Any]] = _safe_data(response) or []
    if used_by_user_id:
        rows = [r for r in rows if str(r.get("used_by_user_id") or "") == str(used_by_user_id)]
    return len(rows)


def _has_prior_paid_payment(*, user_id: str) -> bool:
    if not user_id:
        return False
    supabase = get_supabase_server_client()
    response = supabase.table("payments").select("id,status").eq("user_id", user_id).execute()
    rows = _safe_data(response) or []
    for row in rows:
        if str(row.get("status") or "").strip().lower() == "paid":
            return True
    return False


def _allowed_for_plan(coupon_row: Dict[str, Any], plan_code: str) -> bool:
    allowed = coupon_row.get("allowed_plan_codes")
    if allowed in (None, "", []):
        return True
    if isinstance(allowed, dict):
        values = list(allowed.values())
    elif isinstance(allowed, list):
        values = allowed
    else:
        values = [allowed]
    normalized_allowed = {str(v).strip() for v in values if str(v).strip()}
    return not normalized_allowed or plan_code in normalized_allowed


def validate_coupon_for_checkout(
    *,
    user_id: Optional[str],
    user_email: Optional[str],
    package: Dict[str, Any],
    coupon_code: str,
) -> Dict[str, Any]:
    normalized_code = _normalize_coupon_code(coupon_code)
    original_amount = round(_to_float(package.get("price_brl") or 0), 2)
    plan_code = _resolve_plan_code(package)

    if not normalized_code:
        return {"ok": False, "message": "Informe um cupom para aplicar."}

    coupon = _load_coupon_by_code(normalized_code)
    if not coupon:
        return {"ok": False, "message": "Cupom não encontrado."}

    if not bool(coupon.get("is_active")):
        return {"ok": False, "message": "Este cupom está inativo."}

    now = _utc_now()
    valid_from = _parse_dt(coupon.get("valid_from"))
    valid_until = _parse_dt(coupon.get("valid_until"))
    if valid_from and now < valid_from:
        return {"ok": False, "message": "Este cupom ainda não está válido."}
    if valid_until and now > valid_until:
        return {"ok": False, "message": "Este cupom expirou."}

    if not _allowed_for_plan(coupon, plan_code):
        return {"ok": False, "message": "Este cupom não é válido para este plano."}

    min_purchase_amount = _to_float(coupon.get("min_purchase_amount"), 0.0)
    if min_purchase_amount and original_amount < min_purchase_amount:
        return {"ok": False, "message": "Este cupom exige um valor mínimo para compra."}

    max_total = _to_int(coupon.get("max_uses_total"), 0)
    if max_total and _count_coupon_usages(coupon_id=coupon.get("id")) >= max_total:
        return {"ok": False, "message": "Este cupom atingiu o limite total de usos."}

    max_per_user = _to_int(coupon.get("max_uses_per_user"), 0)
    if max_per_user and user_id and _count_coupon_usages(coupon_id=coupon.get("id"), used_by_user_id=user_id) >= max_per_user:
        return {"ok": False, "message": "Você já atingiu o limite de uso deste cupom."}

    if bool(coupon.get("first_purchase_only")) and user_id and _has_prior_paid_payment(user_id=user_id):
        return {"ok": False, "message": "Este cupom vale apenas para a primeira compra."}

    owner_user_id = str(coupon.get("owner_user_id") or "")
    owner_email = str(coupon.get("owner_email") or "").strip().lower()
    normalized_user_email = str(user_email or "").strip().lower()
    if not bool(coupon.get("can_be_used_by_owner")):
        if owner_user_id and user_id and owner_user_id == str(user_id):
            return {"ok": False, "message": "O dono do cupom não pode usar o próprio cupom."}
        if owner_email and normalized_user_email and owner_email == normalized_user_email:
            return {"ok": False, "message": "O dono do cupom não pode usar o próprio cupom."}

    discount_type = str(coupon.get("discount_type") or "").strip().lower()
    discount_value = round(_to_float(coupon.get("discount_value"), 0.0), 2)
    if discount_type == "percent":
        discount_amount = round(original_amount * (discount_value / 100.0), 2)
    elif discount_type == "fixed":
        discount_amount = round(discount_value, 2)
    else:
        return {"ok": False, "message": "Tipo de desconto inválido no cupom."}

    discount_amount = min(discount_amount, original_amount)
    final_amount = round(max(0.0, original_amount - discount_amount), 2)

    snapshot = {
        "id": coupon.get("id"),
        "code": normalized_code,
        "coupon_type": coupon.get("coupon_type"),
        "discount_type": discount_type,
        "discount_value": discount_value,
        "owner_user_id": coupon.get("owner_user_id"),
        "owner_email": coupon.get("owner_email"),
        "used_by_user_id": user_id,
        "used_by_email": user_email,
        "plan_code": plan_code,
    }

    return {
        "ok": True,
        "message": "Cupom aplicado com sucesso.",
        "coupon": coupon,
        "coupon_id": coupon.get("id"),
        "coupon_code": normalized_code,
        "coupon_owner_user_id": coupon.get("owner_user_id"),
        "discount_type": discount_type,
        "discount_value": discount_value,
        "original_amount": original_amount,
        "discount_amount": discount_amount,
        "final_amount": final_amount,
        "plan_code": plan_code,
        "snapshot": snapshot,
        "normalized_code": normalized_code,
    }


def _normalize_email(value: Any) -> str:
    return str(value or "").strip().lower()




def _resolve_owner_user_id_by_email(owner_email: Optional[str]) -> Optional[str]:
    normalized = _normalize_email(owner_email)
    if not normalized:
        return None

    supabase = get_supabase_server_client()

    # 1) tenta primeiro pela tabela profiles
    try:
        response = supabase.table("profiles").select("id,email").execute()
        rows = _safe_data(response) or []
        for row in rows:
            if _normalize_email(row.get("email")) == normalized:
                owner_id = str(row.get("id") or "").strip()
                if owner_id:
                    return owner_id
    except Exception:
        pass

    # 2) fallback opcional via auth admin, quando disponível com service role
    auth = getattr(supabase, "auth", None)
    admin = getattr(auth, "admin", None) if auth is not None else None
    list_users = getattr(admin, "list_users", None) if admin is not None else None
    if callable(list_users):
        try:
            result = list_users()
            users = getattr(result, "users", None)
            if users is None and isinstance(result, dict):
                users = result.get("users")
            users = users or []
            for user in users:
                email = _normalize_email(getattr(user, "email", None) if not isinstance(user, dict) else user.get("email"))
                if email == normalized:
                    user_id = getattr(user, "id", None) if not isinstance(user, dict) else user.get("id")
                    user_id = str(user_id or "").strip()
                    if user_id:
                        return user_id
        except Exception:
            pass

    return None

def user_can_manage_coupons(user_email: Optional[str]) -> bool:
    normalized = _normalize_email(user_email)
    configured = st.secrets.get("COUPONS_ADMIN_EMAILS", "")
    emails: List[str] = []
    if isinstance(configured, str):
        emails = [_normalize_email(v) for v in configured.split(",") if _normalize_email(v)]
    elif isinstance(configured, (list, tuple)):
        emails = [_normalize_email(v) for v in configured if _normalize_email(v)]

    # Fallback provisório: se não houver configuração, libera apenas usuários logados.
    if not emails:
        return bool(normalized)
    return normalized in set(emails)


def list_coupon_codes(limit: int = 50) -> List[Dict[str, Any]]:
    supabase = get_supabase_server_client()
    response = supabase.table("coupon_codes").select("*").order("created_at", desc=True).limit(limit).execute()
    return _safe_data(response) or []


def list_coupon_usage_rows(*, coupon_code: str = "", owner_email: str = "", payment_status: str = "", limit: int = 200) -> List[Dict[str, Any]]:
    supabase = get_supabase_server_client()
    usage_resp = supabase.table("coupon_usages").select("*").execute()
    usage_rows = _safe_data(usage_resp) or []

    coupons_by_id: Dict[str, Dict[str, Any]] = {}
    coupon_resp = supabase.table("coupon_codes").select("id,code,owner_email").execute()
    coupon_rows = _safe_data(coupon_resp) or []
    for row in coupon_rows:
        coupons_by_id[str(row.get("id"))] = row

    wanted_code = _normalize_coupon_code(coupon_code)
    wanted_owner = _normalize_email(owner_email)
    wanted_status = str(payment_status or "").strip().lower()

    enriched: List[Dict[str, Any]] = []
    for row in usage_rows:
        coupon_row = coupons_by_id.get(str(row.get("coupon_id"))) or {}
        merged = dict(row)
        merged["coupon_code"] = row.get("coupon_code") or coupon_row.get("code")
        merged["owner_email"] = row.get("owner_email") or coupon_row.get("owner_email")

        code_ok = not wanted_code or _normalize_coupon_code(merged.get("coupon_code")) == wanted_code
        owner_ok = not wanted_owner or _normalize_email(merged.get("owner_email")) == wanted_owner
        status_ok = not wanted_status or str(merged.get("payment_status") or "").strip().lower() == wanted_status
        if code_ok and owner_ok and status_ok:
            enriched.append(merged)

    enriched.sort(key=lambda r: str(r.get("confirmed_at") or r.get("created_at") or ""), reverse=True)
    return enriched[:limit]


def summarize_coupon_usage_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_usages = len(rows)
    paid_usages = 0
    total_discount = 0.0
    total_final_amount = 0.0
    for row in rows:
        status = str(row.get("payment_status") or "").strip().lower()
        if status == "paid":
            paid_usages += 1
        total_discount += _to_float(row.get("discount_amount"), 0.0)
        total_final_amount += _to_float(row.get("final_amount"), 0.0)
    return {
        "total_usages": total_usages,
        "paid_usages": paid_usages,
        "total_discount": round(total_discount, 2),
        "total_final_amount": round(total_final_amount, 2),
    }


def create_coupon_code(
    *,
    code: str,
    owner_email: Optional[str],
    coupon_type: str,
    discount_type: str,
    discount_value: float,
    is_active: bool = True,
    valid_from: Optional[datetime] = None,
    valid_until: Optional[datetime] = None,
    max_uses_total: Optional[int] = None,
    max_uses_per_user: Optional[int] = None,
    first_purchase_only: bool = False,
    min_purchase_amount: Optional[float] = None,
    can_be_used_by_owner: bool = False,
    allowed_plan_codes: Optional[List[str]] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    normalized_code = _normalize_coupon_code(code)
    if not normalized_code:
        raise ValueError("Informe um código de cupom.")

    if discount_type not in {"percent", "fixed"}:
        raise ValueError("Tipo de desconto inválido.")

    if coupon_type not in {"public_discount", "referral", "campaign", "manual"}:
        raise ValueError("Tipo de cupom inválido.")

    discount_value = round(_to_float(discount_value), 2)
    if discount_value <= 0:
        raise ValueError("O valor do desconto deve ser maior que zero.")
    if discount_type == "percent" and discount_value > 100:
        raise ValueError("Desconto percentual não pode ser maior que 100.")

    allowed_plan_codes = [str(v).strip() for v in (allowed_plan_codes or []) if str(v).strip()]
    payload = {
        "code": normalized_code,
        "owner_email": _normalize_email(owner_email) or None,
        "owner_user_id": _resolve_owner_user_id_by_email(owner_email),
        "coupon_type": coupon_type,
        "discount_type": discount_type,
        "discount_value": discount_value,
        "is_active": bool(is_active),
        "valid_from": valid_from.isoformat() if valid_from else None,
        "valid_until": valid_until.isoformat() if valid_until else None,
        "max_uses_total": int(max_uses_total) if max_uses_total else None,
        "max_uses_per_user": int(max_uses_per_user) if max_uses_per_user else None,
        "first_purchase_only": bool(first_purchase_only),
        "allowed_plan_codes": allowed_plan_codes or None,
        "min_purchase_amount": round(_to_float(min_purchase_amount), 2) if min_purchase_amount not in (None, "") else None,
        "can_be_used_by_owner": bool(can_be_used_by_owner),
        "notes": str(notes or "").strip() or None,
    }

    supabase = get_supabase_server_client()
    existing = _load_coupon_by_code(normalized_code)
    if existing:
        raise ValueError("Já existe um cupom com esse código.")

    response = supabase.table("coupon_codes").insert(payload).execute()
    rows = _safe_data(response) or []
    if not rows:
        raise RuntimeError("Não foi possível criar o cupom.")
    return rows[0]


def _load_coupon_by_id(coupon_id: Any) -> Optional[Dict[str, Any]]:
    if coupon_id in (None, ""):
        return None
    supabase = get_supabase_server_client()
    response = supabase.table("coupon_codes").select("*").execute()
    rows = _safe_data(response) or []
    wanted = str(coupon_id)
    for row in rows:
        if str(row.get("id")) == wanted:
            return row
    return None


def update_coupon_code(
    *,
    coupon_id: Any,
    owner_email: Optional[str],
    coupon_type: str,
    discount_type: str,
    discount_value: float,
    is_active: bool = True,
    valid_from: Optional[datetime] = None,
    valid_until: Optional[datetime] = None,
    max_uses_total: Optional[int] = None,
    max_uses_per_user: Optional[int] = None,
    first_purchase_only: bool = False,
    allowed_plan_codes: Optional[List[str]] = None,
    min_purchase_amount: Optional[float] = None,
    can_be_used_by_owner: bool = False,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    existing = _load_coupon_by_id(coupon_id)
    if not existing:
        raise ValueError("Cupom não encontrado.")

    if discount_type not in {"percent", "fixed"}:
        raise ValueError("Tipo de desconto inválido.")

    if coupon_type not in {"public_discount", "referral", "campaign", "manual"}:
        raise ValueError("Tipo de cupom inválido.")

    discount_value = round(_to_float(discount_value), 2)
    if discount_value <= 0:
        raise ValueError("O valor do desconto deve ser maior que zero.")
    if discount_type == "percent" and discount_value > 100:
        raise ValueError("Desconto percentual não pode ser maior que 100.")

    if valid_from and valid_until and valid_until < valid_from:
        raise ValueError("A data final não pode ser anterior à data inicial.")

    allowed_plan_codes = [str(v).strip() for v in (allowed_plan_codes or []) if str(v).strip()]
    normalized_owner_email = _normalize_email(owner_email) or None
    payload = {
        "owner_email": normalized_owner_email,
        "owner_user_id": _resolve_owner_user_id_by_email(normalized_owner_email),
        "coupon_type": coupon_type,
        "discount_type": discount_type,
        "discount_value": discount_value,
        "is_active": bool(is_active),
        "valid_from": valid_from.isoformat() if valid_from else None,
        "valid_until": valid_until.isoformat() if valid_until else None,
        "max_uses_total": int(max_uses_total) if max_uses_total else None,
        "max_uses_per_user": int(max_uses_per_user) if max_uses_per_user else None,
        "first_purchase_only": bool(first_purchase_only),
        "allowed_plan_codes": allowed_plan_codes or None,
        "min_purchase_amount": round(_to_float(min_purchase_amount), 2) if min_purchase_amount not in (None, "") else None,
        "can_be_used_by_owner": bool(can_be_used_by_owner),
        "notes": str(notes or "").strip() or None,
    }

    supabase = get_supabase_server_client()
    response = supabase.table("coupon_codes").update(payload).eq("id", coupon_id).execute()
    rows = _safe_data(response) or []
    if rows:
        return rows[0]
    # fallback para clients/stubs que não retornam a linha atualizada
    merged = dict(existing)
    merged.update(payload)
    return merged


def set_coupon_active(*, coupon_id: Any, is_active: bool) -> Dict[str, Any]:
    existing = _load_coupon_by_id(coupon_id)
    if not existing:
        raise ValueError("Cupom não encontrado.")
    supabase = get_supabase_server_client()
    response = supabase.table("coupon_codes").update({"is_active": bool(is_active)}).eq("id", coupon_id).execute()
    rows = _safe_data(response) or []
    if rows:
        return rows[0]
    merged = dict(existing)
    merged["is_active"] = bool(is_active)
    return merged
