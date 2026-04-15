from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_credit_gate_contract_keeps_balance_check_and_inline_plans_trigger() -> None:
    app_py = _read(ROOT / "app.py")
    report_section = _read(ROOT / "ui" / "report" / "section.py")
    checkout_flow = _read(ROOT / "core" / "checkout_flow.py")

    app_required = [
        'get_credit_balance(user_id)',
        'st.session_state.show_inline_payments = True',
        'consume_viability_credit(',
        'amount=1',
    ]
    for item in app_required:
        assert item in app_py, f"Fluxo de crédito do relatório perdeu a âncora crítica: {item}"

    assert 'description="Geração de relatório de viabilidade"' in checkout_flow, (
        "A descrição operacional do débito do relatório deve permanecer no core.checkout_flow."
    )

    section_required = [
        'saldo_atual = get_credit_balance_func(user_id)',
        'st.session_state.show_inline_payments = True',
        'Você não possui créditos suficientes para gerar o relatório.',
        'render_payments_panel_func()',
    ]
    for item in section_required:
        assert item in report_section, f"Seção do relatório perdeu a proteção de saldo/planos inline: {item}"


def test_credit_gate_contract_keeps_generate_button_login_gate() -> None:
    report_section = _read(ROOT / "ui" / "report" / "section.py")

    required = [
        'st.button(',
        '"📄 Gerar Relatório do Estudo de Viabilidade"',
        'key="btn_generate_report"',
        'disabled=(not user_logged_in)',
        'if can_offer_report:',
    ]
    for item in required:
        assert item in report_section, f"Gate visual do relatório perdeu a âncora: {item}"
