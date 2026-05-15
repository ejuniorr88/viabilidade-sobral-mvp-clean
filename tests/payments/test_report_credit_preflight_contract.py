from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_checkout_flow_keeps_credit_preflight_before_report_debit() -> None:
    text = _read(ROOT / "core" / "checkout_flow.py")
    assert 'def preflight_report_credit_balance(' in text
    assert 'preflight_reconcile_credit_func' in text
    assert 'preflight_reconcile_credit_func(user_id_value=user_id_value)' in text
    assert text.index('preflight_reconcile_credit_func(user_id_value=user_id_value)') < text.index('consume_viability_credit_func('), (
        "O checkout do relatório deve tentar reconciliar primeiro o pagamento recém-aprovado "
        "antes do débito do primeiro relatório."
    )


def test_app_uses_report_delivery_preflight_facade() -> None:
    app_text = _read(ROOT / "app.py")
    facade_text = _read(ROOT / "core" / "report_delivery.py")
    section_text = _read(ROOT / "ui" / "report" / "section.py")

    assert 'preflight_report_delivery_credit_balance' in app_text
    assert 'preflight_credit_balance_func=partial(' in app_text
    assert 'preflight_credit_balance_func' in section_text
    assert 'def _preflight_report_credit_balance(' not in app_text

    assert 'checkout_flow_core.preflight_report_credit_balance' in facade_text
    assert 'refresh_payment_status_and_credit_func=refresh_payment_status_and_credit' in facade_text
    assert 'ensure_paid_payment_is_credited_func=ensure_paid_payment_is_credited' in facade_text
