from __future__ import annotations

from typing import Any, Dict, Optional


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def build_discount_coupon_application(
    *,
    coupon: Dict[str, Any],
    normalized_code: str,
    original_amount: float,
    plan_code: str,
    user_id: Optional[str],
    user_email: Optional[str],
) -> Dict[str, Any]:
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
        "benefit_type": "discount",
        "discount_type": discount_type,
        "discount_value": discount_value,
        "bonus_credits": 0,
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
        "benefit_type": "discount",
        "discount_type": discount_type,
        "discount_value": discount_value,
        "bonus_credits": 0,
        "original_amount": original_amount,
        "discount_amount": discount_amount,
        "final_amount": final_amount,
        "plan_code": plan_code,
        "snapshot": snapshot,
        "normalized_code": normalized_code,
    }
