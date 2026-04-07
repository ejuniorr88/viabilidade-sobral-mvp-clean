from __future__ import annotations

from html import escape
from urllib.parse import urlencode


def _nav_href(app_url: str, nav: str) -> str:
    params = urlencode({"vf_nav": nav})
    base = (app_url or "").rstrip("/")
    return f"{base}/?{params}" if base else f"/?{params}"


def build_header_bar_html(app_url: str) -> str:
    brand = '<span class="vf-brand-text">Viabilidade-Fácil<span class="vf-brand-dot">.</span></span>'
    links = [
        ("Como funciona", "how"),
        ("Área do cliente", "client"),
        ("Planos", "plans"),
        ("Dúvida e suporte", "support"),
    ]
    nav_html = "".join(
        f'<a class="vf-header-link" href="{escape(_nav_href(app_url, key), quote=True)}">{escape(label)}</a>'
        for label, key in links
    )
    return (
        '<div class="vf-header-wrap">'
        '  <div class="vf-header-bar">'
        f'    <div class="vf-brand">{brand}</div>'
        f'    <nav class="vf-header-nav" aria-label="Navegação principal">{nav_html}</nav>'
        '  </div>'
        '</div>'
    )
