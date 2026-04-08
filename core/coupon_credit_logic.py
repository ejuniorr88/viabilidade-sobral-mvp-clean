from __future__ import annotations

from typing import Any, Dict, Optional


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def build_credit_coupon_application(
    *,
    coupon: Dict[str, Any],
    normalized_code: str,
    original_amount: float,
    plan_code: str,
    user_id: Optional[str],
    user_email: Optional[str],
) -> Dict[str, Any]:
    bonus_credits = _to_int(coupon.get("bonus_credits"), 0)
    if bonus_credits <= 0:
        return {"ok": False, "message": "Quantidade de créditos bônus inválida no cupom."}

    snapshot = {
        "id": coupon.get("id"),
        "code": normalized_code,
        "coupon_type": coupon.get("coupon_type"),
        "benefit_type": "credit",
        "discount_type": None,
        "discount_value": 0.0,
        "bonus_credits": bonus_credits,
        "owner_user_id": coupon.get("owner_user_id"),
        "owner_email": coupon.get("owner_email"),
        "used_by_user_id": user_id,
        "used_by_email": user_email,
        "plan_code": plan_code,
    }

    return {
        "ok": True,
        "message": f"Cupom aplicado com sucesso. Este cupom adicionará {bonus_credits} crédito(s) bônus após o pagamento.",
        "coupon": coupon,
        "coupon_id": coupon.get("id"),
        "coupon_code": normalized_code,
        "coupon_owner_user_id": coupon.get("owner_user_id"),
        "benefit_type": "credit",
        "discount_type": None,
        "discount_value": 0.0,
        "bonus_credits": bonus_credits,
        "original_amount": original_amount,
        "discount_amount": 0.0,
        "final_amount": original_amount,
        "plan_code": plan_code,
        "snapshot": snapshot,
        "normalized_code": normalized_code,
    }
