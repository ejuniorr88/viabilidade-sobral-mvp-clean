from __future__ import annotations

import html


def build_header_bar_html(app_url: str) -> str:
    app_url = (app_url or "").rstrip("/")
    base = html.escape(app_url or "", quote=True)

    def _href(nav: str) -> str:
        return f"{base}/?vf_nav={nav}" if base else f"/?vf_nav={nav}"

    return f"""
    <div class="vf-header-wrap">
      <div class="vf-header-bar">
        <div class="vf-header-brand">Viabilidade-Fácil<span> .</span></div>
        <div class="vf-header-links">
          <a class="vf-header-link" href="{_href('how')}" target="_self">Como funciona</a>
          <a class="vf-header-link" href="{_href('client')}" target="_self">Área do cliente</a>
          <a class="vf-header-link" href="{_href('plans')}" target="_self">Planos</a>
          <a class="vf-header-link" href="{_href('support')}" target="_self">Dúvida e suporte</a>
        </div>
      </div>
    </div>
    """
