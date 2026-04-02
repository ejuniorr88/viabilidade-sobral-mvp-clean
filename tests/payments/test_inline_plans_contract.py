from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_inline_plans_contract_keeps_runtime_flag_and_payments_panel_hook() -> None:
    app_py = _read(ROOT / "app.py")
    report_section = _read(ROOT / "ui" / "report" / "section.py")

    required_app = [
        'show_inline_payments',
        'render_payments_panel()',
    ]
    for item in required_app:
        assert item in app_py, f"App perdeu a âncora de pagamentos inline: {item}"

    required_section = [
        'if st.session_state.get("show_inline_payments"):',
        'render_payments_panel_func()',
    ]
    for item in required_section:
        assert item in report_section, f"Seção do relatório perdeu a âncora de planos inline: {item}"


def test_inline_plans_contract_keeps_pdf_download_hook_after_report_unlock() -> None:
    report_section = _read(ROOT / "ui" / "report" / "section.py")

    required = [
        'st.download_button(',
        'label="⬇️ Baixar relatório em PDF"',
        'file_name="relatorio_viabilidade.pdf"',
        'key="download_report_pdf"',
    ]
    for item in required:
        assert item in report_section, f"Fluxo de download do PDF perdeu a âncora: {item}"
