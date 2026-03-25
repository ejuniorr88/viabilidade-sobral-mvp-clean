from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='ignore')


def test_gerar_relatorio_flow_contract_keeps_generate_button_and_credit_gate() -> None:
    app_py = _read(ROOT / 'app.py')

    required = [
        'st.subheader("Relatório completo")',
        '"📄 Gerar relatório"',
        'key="btn_generate_report"',
        'disabled=(not user_logged_in)',
        'get_credit_balance(user_id)',
        'consume_viability_credit(',
        'st.session_state.show_inline_payments = True',
        'st.session_state.report_unlocked = True',
        'render_payments_panel()',
        'report_unlocked_signature',
        'pending_report_generation_signature',
        'Você tem certeza que deseja gerar outro relatório?',
        'Isso vai gastar outro crédito.',
        'btn_confirm_generate_other_report',
        'btn_cancel_generate_other_report',
    ]
    for item in required:
        assert item in app_py, f"Fluxo de geração do relatório perdeu a âncora crítica: {item}"



def test_gerar_relatorio_flow_contract_keeps_report_render_pdf_and_save_paths() -> None:
    app_py = _read(ROOT / 'app.py')

    required = [
        'render_analise_section(',
        'render_zone_description_section(calc)',
        'render_relatorio_section(calc)',
        'generate_report_pdf_bytes(',
        'label="⬇️ Baixar relatório em PDF"',
        'file_name="relatorio_viabilidade.pdf"',
        'key="download_report_pdf"',
        'save_client_report(',
        'build_report_signature(',
    ]
    for item in required:
        assert item in app_py, f"Fluxo de render/PDF/salvamento do relatório perdeu a âncora: {item}"



def test_gerar_relatorio_flow_contract_keeps_zone_description_and_figures_hooks() -> None:
    relatorio = _read(ROOT / 'ui' / 'relatorio.py')

    required = [
        'fetch_zone_description',
        'render_figuras_anexo_v',
        'render_dicas_valiosas',
        'render_quadro_tecnico',
        'st.subheader("6) Relatório Urbanístico")',
        'calc.get("ok")',
    ]
    for item in required:
        assert item in relatorio, f"ui/relatorio.py perdeu hook crítico do fluxo de relatório: {item}"


def test_gerar_relatorio_flow_contract_keeps_signature_lock_and_pre_generation_guard() -> None:
    app_py = _read(ROOT / 'app.py')

    required = [
        'current_report_signature = build_report_signature(',
        'report_unlocked_for_current_signature',
        'cached_pdf_matches_current_signature',
        'preview_pdf_bytes = generate_report_pdf_bytes(',
        'st.session_state["last_generated_pdf_bytes"] = preview_pdf_bytes',
        'st.session_state["last_generated_pdf_signature"] = current_report_signature',
        'Não foi possível preparar o relatório antes de descontar o crédito',
    ]
    for item in required:
        assert item in app_py, f"Fluxo de geração do relatório perdeu a proteção crítica: {item}"
