from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")



def test_report_section_keeps_login_balance_and_confirmation_gates() -> None:
    text = _read(ROOT / "ui" / "report" / "section.py")

    required = [
        'st.info("Faça login com Google para gerar o relatório completo.")',
        'get_credit_balance_func(user_id)',
        'st.info(f"Saldo atual: {saldo_atual} crédito(s).")',
        'st.session_state.show_inline_payments = True',
        'st.error("Você não possui créditos suficientes para gerar o relatório.")',
        'confirm_new_report',
        'pending_report_signature',
        '"Sim, gerar outro relatório"',
        'render_payments_panel_func()',
    ]
    for item in required:
        assert item in text, f"ui/report/section.py perdeu gate crítico de login/saldo/confirmação: {item}"
