from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_coupon_runtime_contract_keeps_checkout_validation_hook() -> None:
    payments_panel = _read(ROOT / "ui" / "payments_panel.py")
    required = [
        'from core.coupons import validate_coupon_for_checkout',
        'validate_coupon_for_checkout(',
        'coupon',
    ]
    for item in required:
        assert item in payments_panel, f"Painel de pagamentos perdeu a integração de cupom: {item}"


def test_coupon_runtime_contract_keeps_payment_and_credit_reconciliation_hooks() -> None:
    payments_panel = _read(ROOT / "ui" / "payments_panel.py")

    required = [
        'create_pending_payment_and_pix',
        'refresh_payment_status_and_credit',
        'ensure_paid_payment_is_credited',
        'inspect_payment_credit_status',
    ]
    for item in required:
        assert item in payments_panel, f"Painel de pagamentos perdeu o hook crítico: {item}"


def test_coupon_runtime_contract_keeps_core_coupon_guards() -> None:
    coupons_py = _read(ROOT / "core" / "coupons.py")

    required = [
        'def validate_coupon_for_checkout(',
        '_normalize_coupon_code',
        '_resolve_plan_code',
        'allowed_plan_codes',
        'first_purchase_only',
        'can_be_used_by_owner',
    ]
    for item in required:
        assert item in coupons_py, f"Core de cupom perdeu a âncora crítica: {item}"
