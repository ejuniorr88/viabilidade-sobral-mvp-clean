from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")



def test_gerar_relatorio_flow_contract_keeps_generate_button_and_credit_gate() -> None:
    app_py = _read(ROOT / "app.py")

    required = [
        'st.subheader("Relatório completo")',
        '"📄 Gerar Relatório do Estudo de Viabilidade"',
        'key="btn_generate_report"',
        'disabled=(not user_logged_in)',
        'get_credit_balance(user_id)',
        'render_payments_panel()',
    ]
    for item in required:
        assert item in app_py, f"Fluxo de geração do relatório perdeu a âncora crítica: {item}"

    assert (
        "consume_viability_credit(" in app_py
        or "_prepare_and_consume_pending_report" in app_py
        or "prepare_and_consume" in app_py
    ), "Fluxo de geração do relatório perdeu o caminho de consumo/liberação de crédito."

    assert (
        "st.session_state.show_inline_payments = True" in app_py
        or "show_inline_payments" in app_py
    ), "Fluxo de geração do relatório perdeu o gatilho de pagamentos inline."

    assert (
        "st.session_state.report_unlocked = True" in app_py
        or "report_snapshot_calc" in app_py
        or "confirm_new_report" in app_py
    ), "Fluxo de geração do relatório perdeu o estado de liberação/snapshot do relatório."



def test_gerar_relatorio_flow_contract_keeps_report_render_pdf_and_save_paths() -> None:
    app_py = _read(ROOT / "app.py")

    required = [
        'render_analise_section(',
        'render_zone_description_section(',
        'render_relatorio_section(',
        'generate_report_pdf_bytes(',
        'label="⬇️ Baixar relatório em PDF"',
        'file_name="relatorio_viabilidade.pdf"',
        'key="download_report_pdf"',
        'save_client_report(',
        'build_report_signature(',
    ]
    for item in required:
        assert item in app_py, f"Fluxo de render/PDF/salvamento do relatório perdeu a âncora: {item}"



def test_gerar_relatorio_flow_contract_keeps_new_report_confirmation_hooks() -> None:
    app_py = _read(ROOT / "app.py")

    confirmation_markers = [
        'confirm_new_report',
        'pending_report_signature',
        'btn_confirm_new_report',
        'Sim, gerar outro relatório',
    ]
    legacy_markers = [
        'consume_viability_credit(',
        'st.session_state.report_unlocked = True',
    ]

    assert (
        any(marker in app_py for marker in confirmation_markers)
        or all(marker in app_py for marker in legacy_markers)
    ), (
        "Fluxo de geração do relatório não apresenta nem o fluxo novo de confirmação, "
        "nem o fluxo legado mínimo de liberação do relatório."
    )



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
