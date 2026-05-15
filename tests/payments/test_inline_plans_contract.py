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


def test_inline_plans_contract_keeps_current_pdf_download_flow_after_report_unlock() -> None:
    """Protege o fluxo atual de PDF sem prender ao motor antigo.

    O fluxo consolidado gera primeiro o PDF visual do snapshot e depois expõe
    o botão de download. Este contrato protege o comportamento visível e aceita
    a chave atual do PDF visual, preservando compatibilidade com a chave antiga
    caso algum ambiente ainda esteja no fluxo técnico anterior.
    """
    report_section = _read(ROOT / "ui" / "report" / "section.py")

    required_any_generation_anchor = [
        '📄 Gerar relatório em PDF',
        'generate_snapshot_pdf_bytes',
        'generate_report_pdf_bytes_func',
    ]
    assert any(item in report_section for item in required_any_generation_anchor), (
        "Fluxo de PDF perdeu a âncora de geração atual ou o fallback técnico."
    )

    required_download_anchors = [
        'st.download_button(',
        'file_name="relatorio_viabilidade.pdf"',
    ]
    for item in required_download_anchors:
        assert item in report_section, f"Fluxo de download do PDF perdeu a âncora: {item}"

    allowed_download_keys = [
        'key="download_report_pdf_visual_ready"',
        'key="download_report_pdf"',
    ]
    assert any(item in report_section for item in allowed_download_keys), (
        "Fluxo de download do PDF perdeu a chave do botão de download atual."
    )
