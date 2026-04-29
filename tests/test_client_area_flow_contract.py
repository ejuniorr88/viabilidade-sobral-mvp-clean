from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='ignore')


def test_client_area_flow_contract_keeps_entry_and_return_paths() -> None:
    app_py = _read(ROOT / 'app.py')
    access_gates = _read(ROOT / 'ui' / 'access_gates.py')
    app_shell = _read(ROOT / 'ui' / 'app_shell.py')

    required = [
        'if st.session_state.get("show_client_area"):',
        'render_client_area_page(',
        'if st.button("← Voltar para o estudo", key="client_area_back")',
        'if st.button("← Voltar para o estudo", key="client_area_back_guest")',
        'st.session_state["show_client_area"] = False',
        'st.markdown("## Área do cliente")',
    ]
    haystack = app_py + '\n' + access_gates + '\n' + app_shell
    for item in required:
        assert item in haystack, f"Fluxo principal da Área do cliente perdeu a âncora: {item}"


def test_client_area_flow_contract_keeps_identity_credit_and_reports_cards() -> None:
    client_area = _read(ROOT / 'ui' / 'client_area.py')

    required = [
        '_info_card("Nome"',
        '_info_card("E-mail"',
        '_info_card("Créditos"',
        'st.markdown("### Relatórios salvos")',
        'list_client_reports(user_id)',
        'return dt.strftime("%d/%m/%Y"), dt.strftime("%H:%M")',
    ]
    for item in required:
        assert item in client_area, f"Área do cliente perdeu informação crítica consolidada: {item}"


def test_client_area_flow_contract_keeps_visual_pdf_download_path() -> None:
    client_area = _read(ROOT / 'ui' / 'client_area.py')

    required = [
        'snapshot_pdf_module',
        'generate_snapshot_html_bytes',
        'generate_snapshot_pdf_bytes',
        'snapshot_file_stem',
        '📄 Gerar relatório em PDF',
        'Gerando relatório, aguarde alguns segundos para fazer o download.',
        '⬇️ Fazer download',
        'Zona:',
        'Rua:',
        'Data:',
        'Horário:',
    ]
    for item in required:
        assert item in client_area, f"Fluxo de PDF visual/listagem da Área do cliente perdeu a âncora: {item}"

    assert 'Baixar PDF salvo antigo' not in client_area
