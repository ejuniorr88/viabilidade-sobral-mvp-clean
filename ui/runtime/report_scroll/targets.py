from __future__ import annotations

REPORT_SCROLL_TARGETS = {
    # Mantém a confirmação blindada em section.py e trata o enquadramento visual
    # do pós-clique em módulo próprio de runtime.
    'report_review_confirm': {'element_id': 'report-review-confirm-start', 'offset': 0},
    # Aviso amarelo de cenário alterado após já existir relatório gerado.
    'report_section_notice': {'element_id': 'report-section-scenario-notice', 'offset': 520},
}
