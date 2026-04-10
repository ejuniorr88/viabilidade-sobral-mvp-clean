from __future__ import annotations

from html import escape as _html_escape
from typing import Any, Sequence

import streamlit as st

SHARED_CSS_INNER = """
:root {
  --vf-ink:#1f2937; --vf-muted:#6b7280; --vf-line:#e2e8f0;
  --vf-brand:#1d4ed8; --vf-navy:#1e293b;
  --vf-success:#166534; --vf-success-bg:#f0fdf4; --vf-success-border:#bbf7d0;
  --vf-warning:#9a3412; --vf-warning-bg:#fff7ed; --vf-warning-border:#fed7aa;
  --vf-danger:#991b1b; --vf-danger-bg:#fef2f2; --vf-danger-border:#fecaca;
}
.vf-report-container { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: var(--vf-ink); font-size: 14px; line-height: 1.6; }
.vf-hero { background: linear-gradient(135deg, #1e293b 0%, #1d4ed8 100%); color: white; border-radius: 16px; padding: 22px 24px; margin-bottom: 20px; page-break-inside: avoid; }
.vf-hero-title { font-size: 26px; font-weight: 800; margin: 0 0 6px 0; line-height: 1.1; }
.vf-hero-subtitle { font-size: 13px; opacity: 0.92; margin:0; }
.vf-hero-meta { font-size:11px; margin-top:12px; opacity:.84; }
.vf-section-card { background:#fff; border:1px solid var(--vf-line); border-radius:16px; padding:18px 20px; margin-bottom:18px; box-shadow:0 4px 12px rgba(0,0,0,.03); page-break-inside: avoid; }
.vf-section-head { display:flex; align-items:center; gap:12px; border-bottom:1px solid var(--vf-line); padding-bottom:12px; margin-bottom:16px; }
.vf-section-badge { width:32px; height:32px; border-radius:50%; background:linear-gradient(135deg,#2563eb 0%,#1e293b 100%); color:white; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:13px; flex-shrink:0; }
.vf-section-title { font-size:18px; font-weight:800; color:var(--vf-navy); margin:0; line-height:1.25; }
.vf-lead { font-size:14px; color:#334155; margin:0 0 12px 0; }
.vf-info-box { padding:16px; border-radius:10px; border:1px solid var(--vf-line); background:#f8fafc; margin:0 0 12px 0; page-break-inside: avoid; }
.vf-info-box.success { background:var(--vf-success-bg); border-color:var(--vf-success-border); color:var(--vf-success); }
.vf-info-box.warning { background:var(--vf-warning-bg); border-color:var(--vf-warning-border); color:var(--vf-warning); }
.vf-info-box.danger { background:var(--vf-danger-bg); border-color:var(--vf-danger-border); color:var(--vf-danger); }
.vf-info-title { font-weight:700; margin-bottom:8px; font-size:15px; }
.vf-formula-box { padding:12px 16px; background:#f1f5f9; border-left:4px solid var(--vf-brand); border-radius:6px; font-family: monospace; font-size:14px; font-weight:bold; margin:0 0 12px 0; color:var(--vf-navy); page-break-inside: avoid; }
.vf-grid { display:flex; flex-wrap:wrap; gap:12px; margin-bottom:14px; }
.vf-summary-card { background:#f8fafc; border:1px solid var(--vf-line); border-radius:10px; padding:12px; flex:1 1 calc(33.333% - 12px); min-width:140px; }
.vf-summary-card.status-success { background:var(--vf-success-bg); border-color:var(--vf-success-border); }
.vf-summary-card.status-warning { background:var(--vf-warning-bg); border-color:var(--vf-warning-border); }
.vf-summary-card.status-danger { background:var(--vf-danger-bg); border-color:var(--vf-danger-border); }
.vf-summary-label { font-size:11px; text-transform:uppercase; color:var(--vf-muted); font-weight:bold; margin-bottom:4px; }
.vf-summary-value { font-size:16px; font-weight:800; color:var(--vf-navy); line-height:1.35; }
.vf-table-wrap { margin-bottom:12px; overflow:hidden; border:1px solid var(--vf-line); border-radius:12px; }
.vf-table { width:100%; border-collapse:collapse; font-size:13px; }
.vf-table th { background:#edf4ff; color:#1f3b69; text-align:left; font-weight:800; padding:9px 10px; border-bottom:1px solid var(--vf-line); }
.vf-table td { padding:8px 10px; border-bottom:1px solid #edf1f5; vertical-align:top; }
.vf-table tbody tr:nth-child(even) td { background:#fbfdff; }
.vf-checklist { margin:0; padding-left:18px; }
.vf-checklist li { margin-bottom:6px; }
.vf-muted { color:var(--vf-muted); }
@media print {
  .vf-section-card, .vf-info-box, .vf-formula-box, .vf-hero, .vf-summary-card { page-break-inside: avoid; }
}
"""

SHARED_CSS = f"<style>{SHARED_CSS_INNER}</style>"


def _html(v: Any) -> str:
    return _html_escape(str(v if v is not None else ""), quote=True)


def ensure_streamlit_report_styles() -> None:
    key = "_vf_report_components_css_loaded"
    if not st.session_state.get(key):
        st.markdown(SHARED_CSS, unsafe_allow_html=True)
        st.session_state[key] = True


def render_html_fragment(fragment_html: str) -> None:
    ensure_streamlit_report_styles()
    st.markdown(fragment_html, unsafe_allow_html=True)


def render_hero(title: str, subtitle: str, meta: str = "") -> str:
    return f'''<div class="vf-hero"><h1 class="vf-hero-title">{_html(title)}</h1><p class="vf-hero-subtitle">{_html(subtitle)}</p>{f'<div class="vf-hero-meta">{_html(meta)}</div>' if meta else ''}</div>'''


def render_section_card(number: int, title: str, body_html: str) -> str:
    return f'''<div class="vf-section-card"><div class="vf-section-head"><div class="vf-section-badge">{number:02d}</div><h2 class="vf-section-title">{_html(title)}</h2></div><div class="vf-section-body">{body_html}</div></div>'''


def render_info_box(title: str, content_html: str, tone: str = "default") -> str:
    tone_cls = tone if tone in {"default", "success", "warning", "danger"} else "default"
    return f'''<div class="vf-info-box {tone_cls}"><div class="vf-info-title">{_html(title)}</div><div class="vf-info-content">{content_html}</div></div>'''


def render_formula_box(text: str) -> str:
    return f'<div class="vf-formula-box">👉 {_html(text)}</div>'


def render_summary_grid(items: Sequence[tuple[str, str, str | None]] | Sequence[tuple[str, str]]) -> str:
    cards = []
    for item in items:
        if len(item) == 3:
            k, v, tone = item  # type: ignore[misc]
        else:
            k, v = item  # type: ignore[misc]
            tone = None
        tone_cls = f' status-{tone}' if tone in {"success", "warning", "danger"} else ''
        cards.append(f'<div class="vf-summary-card{tone_cls}"><div class="vf-summary-label">{_html(k)}</div><div class="vf-summary-value">{_html(v)}</div></div>')
    return f'<div class="vf-grid">{"".join(cards)}</div>'


def render_table_block(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    thead = ''.join(f'<th>{_html(h)}</th>' for h in headers)
    body = ''.join('<tr>' + ''.join(f'<td>{_html(cell)}</td>' for cell in row) + '</tr>' for row in rows)
    return f'<div class="vf-table-wrap"><table class="vf-table"><thead><tr>{thead}</tr></thead><tbody>{body}</tbody></table></div>'


def render_checklist_block(items: Sequence[str]) -> str:
    lis = ''.join(f'<li>{_html(item)}</li>' for item in items if str(item or '').strip())
    return f'<ul class="vf-checklist">{lis}</ul>'
