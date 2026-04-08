from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import streamlit as st
from supabase import Client, create_client

from core.coupon_credit_logic import build_credit_coupon_application
from core.coupon_discount_logic import build_discount_coupon_application


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


def _normalize_email(value: Any) -> str:
    return str(value or "").strip().lower()


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




def _resolve_coupon_benefit_type(coupon_row: Dict[str, Any]) -> str:
    value = str(coupon_row.get("benefit_type") or coupon_row.get("reward_type") or "discount").strip().lower()
    return value if value in {"discount", "credit"} else "discount"


def _normalize_discount_fields(*, benefit_type: str, discount_type: Optional[str], discount_value: Any) -> tuple[Optional[str], float]:
    normalized_benefit = str(benefit_type or "discount").strip().lower()
    if normalized_benefit == "credit":
        return "fixed", 0.01
    normalized_discount_type = str(discount_type or "fixed").strip().lower()
    if normalized_discount_type not in {"fixed", "percent"}:
        normalized_discount_type = "fixed"
    return normalized_discount_type, round(_to_float(discount_value, 0.0), 2)


def _normalize_bonus_credits(*, benefit_type: str, bonus_credits: Any) -> int:
    normalized_benefit = str(benefit_type or "discount").strip().lower()
    if normalized_benefit != "credit":
        return 0
    credits = _to_int(bonus_credits, 0)
    return max(0, credits)

def _resolve_owner_user_id_by_email(owner_email: Optional[str]) -> Optional[str]:
    normalized = _normalize_email(owner_email)
    if not normalized:
        return None

    supabase = get_supabase_server_client()

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

    benefit_type = _resolve_coupon_benefit_type(coupon)
    if benefit_type == "credit":
        return build_credit_coupon_application(
            coupon=coupon,
            normalized_code=normalized_code,
            original_amount=original_amount,
            plan_code=plan_code,
            user_id=user_id,
            user_email=user_email,
        )

    return build_discount_coupon_application(
        coupon=coupon,
        normalized_code=normalized_code,
        original_amount=original_amount,
        plan_code=plan_code,
        user_id=user_id,
        user_email=user_email,
    )


def user_can_manage_coupons(user_email: Optional[str]) -> bool:
    normalized = _normalize_email(user_email)
    configured = st.secrets.get("COUPONS_ADMIN_EMAILS", "")
    emails: List[str] = []
    if isinstance(configured, str):
        emails = [_normalize_email(v) for v in configured.split(",") if _normalize_email(v)]
    elif isinstance(configured, list):
        emails = [_normalize_email(v) for v in configured if _normalize_email(v)]

    # Sem admins configurados, ninguém pode acessar a área.
    if not emails:
        return False
    return normalized in emails


def _paid_coupon_usage_count(*, coupon_id: Any) -> int:
    supabase = get_supabase_server_client()
    response = supabase.table("coupon_usages").select("*").eq("coupon_id", coupon_id).execute()
    rows: List[Dict[str, Any]] = _safe_data(response) or []
    return sum(1 for r in rows if str(r.get("payment_status") or "").strip().lower() == "paid")


def coupon_has_paid_usage(*, coupon_id: Any) -> bool:
    return _paid_coupon_usage_count(coupon_id=coupon_id) > 0


def _locked_coupon_payload_if_paid_usage(*, existing_row: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    if not coupon_has_paid_usage(coupon_id=existing_row.get("id")):
        return payload

    locked_fields = [
        "code",
        "owner_email",
        "owner_user_id",
        "coupon_type",
        "benefit_type",
        "discount_type",
        "discount_value",
        "bonus_credits",
    ]
    protected = dict(payload)
    for field in locked_fields:
        protected[field] = existing_row.get(field)
    return protected


def create_coupon_code(
    *,
    code: str,
    owner_email: Optional[str],
    coupon_type: str,
    benefit_type: str = "discount",
    discount_type: Optional[str] = "fixed",
    discount_value: float = 0.0,
    bonus_credits: Optional[int] = None,
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
    normalized_code = _normalize_coupon_code(code)
    if not normalized_code:
        raise ValueError("Informe um código de cupom válido.")

    normalized_owner_email = _normalize_email(owner_email)
    owner_user_id = _resolve_owner_user_id_by_email(normalized_owner_email)

    supabase = get_supabase_server_client()
    existing = supabase.table("coupon_codes").select("*").execute()
    rows = _safe_data(existing) or []
    for row in rows:
        if _normalize_coupon_code(row.get("code")) == normalized_code:
            raise ValueError("Já existe um cupom com esse código.")

    normalized_benefit_type = _resolve_coupon_benefit_type({"benefit_type": benefit_type})
    normalized_discount_type, normalized_discount_value = _normalize_discount_fields(
        benefit_type=normalized_benefit_type,
        discount_type=discount_type,
        discount_value=discount_value,
    )
    normalized_bonus_credits = _normalize_bonus_credits(benefit_type=normalized_benefit_type, bonus_credits=bonus_credits)

    payload = {
        "code": normalized_code,
        "owner_user_id": owner_user_id,
        "owner_email": normalized_owner_email or None,
        "coupon_type": coupon_type,
        "benefit_type": normalized_benefit_type,
        "discount_type": normalized_discount_type,
        "discount_value": normalized_discount_value,
        "bonus_credits": normalized_bonus_credits,
        "is_active": bool(is_active),
        "valid_from": valid_from.isoformat() if isinstance(valid_from, datetime) else valid_from,
        "valid_until": valid_until.isoformat() if isinstance(valid_until, datetime) else valid_until,
        "max_uses_total": max_uses_total,
        "max_uses_per_user": max_uses_per_user,
        "first_purchase_only": bool(first_purchase_only),
        "allowed_plan_codes": allowed_plan_codes or None,
        "min_purchase_amount": round(float(min_purchase_amount), 2) if min_purchase_amount not in (None, "") else None,
        "can_be_used_by_owner": bool(can_be_used_by_owner),
        "notes": notes or None,
    }
    response = supabase.table("coupon_codes").insert(payload).execute()
    data = _safe_data(response) or []
    return data[0] if data else payload


def update_coupon_code(
    *,
    coupon_id: Any,
    code: str,
    owner_email: Optional[str],
    coupon_type: str,
    benefit_type: str = "discount",
    discount_type: Optional[str] = "fixed",
    discount_value: float = 0.0,
    bonus_credits: Optional[int] = None,
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
    normalized_code = _normalize_coupon_code(code)
    if not normalized_code:
        raise ValueError("Informe um código de cupom válido.")

    normalized_owner_email = _normalize_email(owner_email)
    owner_user_id = _resolve_owner_user_id_by_email(normalized_owner_email)

    supabase = get_supabase_server_client()
    existing = supabase.table("coupon_codes").select("*").execute()
    rows = _safe_data(existing) or []

    for row in rows:
        if str(row.get("id")) != str(coupon_id) and _normalize_coupon_code(row.get("code")) == normalized_code:
            raise ValueError("Já existe um cupom com esse código.")

    normalized_benefit_type = _resolve_coupon_benefit_type({"benefit_type": benefit_type})
    normalized_discount_type, normalized_discount_value = _normalize_discount_fields(
        benefit_type=normalized_benefit_type,
        discount_type=discount_type,
        discount_value=discount_value,
    )
    normalized_bonus_credits = _normalize_bonus_credits(benefit_type=normalized_benefit_type, bonus_credits=bonus_credits)

    payload = {
        "code": normalized_code,
        "owner_user_id": owner_user_id,
        "owner_email": normalized_owner_email or None,
        "coupon_type": coupon_type,
        "benefit_type": normalized_benefit_type,
        "discount_type": normalized_discount_type,
        "discount_value": normalized_discount_value,
        "bonus_credits": normalized_bonus_credits,
        "is_active": bool(is_active),
        "valid_from": valid_from.isoformat() if isinstance(valid_from, datetime) else valid_from,
        "valid_until": valid_until.isoformat() if isinstance(valid_until, datetime) else valid_until,
        "max_uses_total": max_uses_total,
        "max_uses_per_user": max_uses_per_user,
        "first_purchase_only": bool(first_purchase_only),
        "allowed_plan_codes": allowed_plan_codes or None,
        "min_purchase_amount": round(float(min_purchase_amount), 2) if min_purchase_amount not in (None, "") else None,
        "can_be_used_by_owner": bool(can_be_used_by_owner),
        "notes": notes or None,
    }

    existing_row = next((row for row in rows if str(row.get("id")) == str(coupon_id)), None) or {}
    payload = _locked_coupon_payload_if_paid_usage(existing_row=existing_row, payload=payload)

    response = (
        supabase.table("coupon_codes")
        .update(payload)
        .eq("id", coupon_id)
        .execute()
    )
    data = _safe_data(response) or []
    return data[0] if data else payload


def set_coupon_active(*, coupon_id: Any, is_active: bool) -> Dict[str, Any]:
    supabase = get_supabase_server_client()
    response = (
        supabase.table("coupon_codes")
        .update({"is_active": bool(is_active)})
        .eq("id", coupon_id)
        .execute()
    )
    data = _safe_data(response) or []
    return data[0] if data else {"id": coupon_id, "is_active": bool(is_active)}


def list_coupon_codes(*, limit: int = 100) -> List[Dict[str, Any]]:
    supabase = get_supabase_server_client()
    response = (
        supabase.table("coupon_codes")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return _safe_data(response) or []


def list_coupon_usages_enriched(*, limit: int = 200) -> List[Dict[str, Any]]:
    supabase = get_supabase_server_client()
    usages_resp = (
        supabase.table("coupon_usages")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    usage_rows: List[Dict[str, Any]] = _safe_data(usages_resp) or []

    coupons_resp = supabase.table("coupon_codes").select("id,code,owner_email").execute()
    coupon_rows = _safe_data(coupons_resp) or []
    coupons_by_id = {str(r.get("id")): r for r in coupon_rows}

    enriched: List[Dict[str, Any]] = []
    for row in usage_rows:
        coupon = coupons_by_id.get(str(row.get("coupon_id")))
        enriched.append(
            {
                **row,
                "coupon_code": row.get("coupon_code") or (coupon or {}).get("code"),
                "owner_email": (coupon or {}).get("owner_email"),
            }
        )
    return enriched


def filter_coupon_usages(
    rows: List[Dict[str, Any]],
    *,
    coupon_code: str = "",
    owner_email: str = "",
    payment_status: str = "",
) -> List[Dict[str, Any]]:
    normalized_code = _normalize_coupon_code(coupon_code)
    normalized_owner = _normalize_email(owner_email)
    normalized_status = str(payment_status or "").strip().lower()

    filtered = rows
    if normalized_code:
        filtered = [r for r in filtered if _normalize_coupon_code(r.get("coupon_code")) == normalized_code]
    if normalized_owner:
        filtered = [r for r in filtered if _normalize_email(r.get("owner_email")) == normalized_owner]
    if normalized_status:
        filtered = [r for r in filtered if str(r.get("payment_status") or "").strip().lower() == normalized_status]
    return filtered


def summarize_coupon_usages(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_uses = len(rows)
    paid_rows = [r for r in rows if str(r.get("payment_status") or "").strip().lower() == "paid"]
    total_paid_uses = len(paid_rows)
    total_discount = round(sum(_to_float(r.get("discount_amount"), 0.0) for r in rows), 2)
    total_final_amount = round(sum(_to_float(r.get("final_amount"), 0.0) for r in rows), 2)

    return {
        "total_uses": total_uses,
        "total_paid_uses": total_paid_uses,
        "total_discount": total_discount,
        "total_final_amount": total_final_amount,
    }


def list_coupon_codes_enriched(*, limit: int = 100) -> List[Dict[str, Any]]:
    rows = list_coupon_codes(limit=limit)
    usage_rows = list_coupon_usages_enriched(limit=1000)

    by_coupon: Dict[str, Dict[str, Any]] = {}
    for usage in usage_rows:
        code = _normalize_coupon_code(usage.get("coupon_code"))
        if not code:
            continue
        bucket = by_coupon.setdefault(code, {"paid_uses": 0, "total_uses": 0, "last_confirmed_at": None})
        bucket["total_uses"] += 1
        if str(usage.get("payment_status") or "").strip().lower() == "paid":
            bucket["paid_uses"] += 1
        confirmed = usage.get("confirmed_at") or usage.get("created_at")
        if confirmed and (bucket["last_confirmed_at"] is None or str(confirmed) > str(bucket["last_confirmed_at"])):
            bucket["last_confirmed_at"] = confirmed

    enriched: List[Dict[str, Any]] = []
    now = _utc_now()
    for row in rows:
        current = dict(row)
        stats = by_coupon.get(_normalize_coupon_code(row.get("code")), {})
        current["paid_uses"] = stats.get("paid_uses", 0)
        current["total_uses"] = stats.get("total_uses", 0)
        current["last_confirmed_at"] = stats.get("last_confirmed_at")
        current["benefit_type"] = _resolve_coupon_benefit_type(current)
        current["bonus_credits"] = _to_int(current.get("bonus_credits"), 0)

        valid_until = _parse_dt(row.get("valid_until"))
        is_expired = bool(valid_until and now > valid_until)
        current["is_expired"] = is_expired
        current["owner_resolved"] = bool(row.get("owner_user_id"))
        current["paid_usage_locked"] = bool(stats.get("paid_uses", 0) > 0)
        enriched.append(current)

    return enriched
