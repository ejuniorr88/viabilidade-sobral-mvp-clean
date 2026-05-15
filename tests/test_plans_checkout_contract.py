from pathlib import Path


def test_plans_page_keeps_reports_exclusive_to_client_area() -> None:
    text = Path("ui/plans/page.py").read_text(encoding="utf-8")

    assert '## Adquirir planos' in text
    assert 'Os relatórios para download continuam exclusivos da Área do Cliente.' in text
    assert 'render_payments_panel()' in text


def test_payments_panel_contract_does_not_render_recent_history_blocks() -> None:
    text = Path("ui/payments_panel.py").read_text(encoding="utf-8")

    assert 'def _render_recent_ledger(' in text
    assert 'def _render_recent_payments(' in text
    assert '_render_recent_ledger(' not in text.split('def render_payments_panel', 1)[1]
    assert '_render_recent_payments(' not in text.split('def render_payments_panel', 1)[1]
    assert 'Os blocos "Extrato recente de créditos" e "Pagamentos recentes"' in text


def test_payments_panel_keeps_local_close_button_for_current_payment() -> None:
    text = Path("ui/payments_panel.py").read_text(encoding="utf-8")

    assert 'close_label = "Cancelar / fechar Pix atual" if status == "pending" else "Fechar pagamento atual"' in text
    assert 'if st.button(close_label, key=f"close_current_payment_{payment_id}", use_container_width=True):' in text
    assert 'clear_all_checkout_states()' in text


def test_client_area_stays_free_from_payments_panel_rendering() -> None:
    text = Path("ui/client_area.py").read_text(encoding="utf-8")

    assert 'render_payments_panel(' not in text
    assert 'Você ainda não possui relatórios salvos na sua área do cliente.' in text
    assert 'Visualização salva do relatório' in text
