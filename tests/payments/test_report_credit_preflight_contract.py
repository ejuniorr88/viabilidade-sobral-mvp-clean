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


def test_app_and_report_section_keep_preflight_credit_hook_without_new_local_helper() -> None:
    app_text = _read(ROOT / "app.py")
    section_text = _read(ROOT / "ui" / "report" / "section.py")

    assert 'checkout_flow_core.preflight_report_credit_balance' in app_text
    assert 'preflight_reconcile_credit_func=preflight_credit_balance' in app_text
    assert 'preflight_credit_balance_func=partial(' in app_text
    assert 'preflight_credit_balance_func' in section_text
    assert 'def _preflight_report_credit_balance(' not in app_text
