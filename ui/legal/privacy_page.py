from __future__ import annotations

from ui.legal.content import PRIVACY_LAST_UPDATED, PRIVACY_POLICY_TEXT
from ui.legal.page_common import render_legal_document_page


def render_privacy_page() -> None:
    render_legal_document_page(
        title="Política de Privacidade",
        subtitle=f"Viabilidade Fácil • Última atualização: {PRIVACY_LAST_UPDATED}",
        body_markdown=PRIVACY_POLICY_TEXT,
    )
