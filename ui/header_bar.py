from __future__ import annotations

from html import escape


def build_header_bar_html(*, app_url: str) -> str:
    client_href = f"{app_url}?vf_nav=client"
    return f"""
    <div class="vf-header-wrap">
      <div class="vf-header-bar">
        <div class="vf-header-brand">Viabilidade-Fácil<span class="vf-header-dot">.</span></div>
        <nav class="vf-header-nav" aria-label="Navegação principal">
          <span class="vf-header-link">Como funciona</span>
          <a class="vf-header-link" href="{escape(client_href, quote=True)}">Área do cliente</a>
          <span class="vf-header-link">Planos</span>
          <span class="vf-header-link">Dúvida e suporte</span>
        </nav>
      </div>
    </div>
    """
