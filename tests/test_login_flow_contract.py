from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='ignore')


def test_client_area_flow_contract_keeps_entry_and_return_paths() -> None:
    app_py = _read(ROOT / 'app.py')

    required = [
        'if st.session_state.get("show_client_area"):',
        'render_client_area_page(',
        'if st.button("← Voltar para o estudo", key="client_area_back")',
        'if st.button("← Voltar para o estudo", key="client_area_back_guest")',
        'st.session_state["show_client_area"] = False',
        'st.markdown("## Área do cliente")',
    ]
    for item in required:
        assert item in app_py, f"Fluxo principal da Área do cliente perdeu a âncora: {item}"


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



def test_client_area_flow_contract_keeps_report_download_path() -> None:
    client_area = _read(ROOT / 'ui' / 'client_area.py')

    required = [
        'build_download_signed_url(path)',
        'st.link_button("⬇️ Fazer download", signed_url, use_container_width=True)',
        'st.button("⬇️ Fazer download", disabled=True, use_container_width=True',
        'Zona:',
        'Rua:',
        'Data:',
        'Horário:',
    ]
    for item in required:
        assert item in client_area, f"Fluxo de download/listagem da Área do cliente perdeu a âncora: {item}"
