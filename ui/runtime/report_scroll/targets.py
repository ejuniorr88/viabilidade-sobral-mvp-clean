from __future__ import annotations

REPORT_SCROLL_TARGETS = {
    # Pós-clique no botão de gerar relatório: enquadra melhor o bloco de
    # confirmação/revisão sem precisar alterar a section.py blindada.
    "report_review_confirm": {"element_id": "report-review-confirm-start", "offset": 120},
    # Aviso amarelo de cenário alterado após já existir relatório gerado.
    "report_section_notice": {"element_id": "report-section-scenario-notice", "offset": 360},
}
