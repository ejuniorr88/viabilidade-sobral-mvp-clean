from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_report_debit_contract_keeps_single_credit_debit_inside_prepare_helper() -> None:
    app_py = _read(ROOT / "app.py")

    match = re.search(
        r"def _prepare_and_consume_report\((.*?)return debit_result, pdf_bytes",
        app_py,
        re.S,
    )
    assert match, "Helper _prepare_and_consume_report não encontrado no app.py."

    body = match.group(0)
    assert body.count("consume_viability_credit(") == 1, (
        "O helper de geração do relatório deve manter um único débito explícito "
        "de crédito para evitar consumo duplicado."
    )

    required = [
        'generate_report_pdf_bytes(calc=calc_ref, session_state=session_snapshot)',
        'consume_viability_credit(',
        'amount=1',
        'save_client_report(',
        'last_saved_report_signature',
    ]
    for item in required:
        assert item in body, f"O helper de geração/consumo perdeu a âncora: {item}"


def test_report_debit_contract_keeps_confirmation_hooks_before_new_generation() -> None:
    app_py = _read(ROOT / "app.py")

    required = [
        'confirm_new_report',
        'pending_report_signature',
        'btn_confirm_new_report_yes',
        'btn_confirm_new_report_no',
        'Sim, gerar outro relatório',
    ]
    for item in required:
        assert item in app_py, f"Fluxo de confirmação para novo relatório perdeu a âncora: {item}"
