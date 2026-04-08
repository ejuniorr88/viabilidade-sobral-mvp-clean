from __future__ import annotations

from ui.legal.content import TERMS_LAST_UPDATED, TERMS_OF_USE_TEXT
from ui.legal.page_common import render_legal_document_page


def render_terms_page() -> None:
    render_legal_document_page(
        title="Termos de Uso",
        subtitle=f"Viabilidade Fácil • Última atualização: {TERMS_LAST_UPDATED}",
        body_markdown=TERMS_OF_USE_TEXT,
    )
