from __future__ import annotations

import html
import importlib
import json
import os
import pkgutil
import re
from contextlib import contextmanager
from copy import deepcopy
from typing import Any, Dict, Iterable


class SnapshotPdfUnavailable(RuntimeError):
    """Raised when the environment cannot render the real snapshot HTML to PDF."""


def _safe_str(value: Any, default: str = "—") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _slug_id(value: Any) -> str:
    raw = str(value or "salvo")
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", raw).strip("_") or "salvo"


def _inline_markdown(text: Any) -> str:
    escaped = html.escape(_safe_str(text), quote=False)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\[(.+?)\]\((https?://[^)]+)\)", r"<a href='\2'>\1</a>", escaped)
    return escaped


def _markdown_table_to_html(lines: list[str]) -> str:
    rows: list[list[str]] = []
    for line in lines:
        stripped = line.strip().strip("|")
        if not stripped:
            continue
        cells = [c.strip() for c in stripped.split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", c or "") for c in cells):
            continue
        rows.append(cells)
    if not rows:
        return ""
    head = rows[0]
    body = rows[1:]
    out = ["<table class='snapshot-table'><thead><tr>"]
    for cell in head:
        out.append(f"<th>{_inline_markdown(cell)}</th>")
    out.append("</tr></thead><tbody>")
    for row in body:
        out.append("<tr>")
        for cell in row:
            out.append(f"<td>{_inline_markdown(cell)}</td>")
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def _markdown_to_html(markdown: Any, *, allow_raw_html: bool = False) -> str:
    text = _safe_str(markdown, "")
    if not text:
        return ""
    if allow_raw_html and "<" in text and ">" in text:
        return text

    lines = text.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    table_buffer: list[str] = []

    def flush_table() -> None:
        nonlocal table_buffer
        if table_buffer:
            out.append(_markdown_table_to_html(table_buffer))
            table_buffer = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            table_buffer.append(stripped)
            continue
        flush_table()

        if not stripped:
            out.append("<br />")
            continue
        if stripped == "---":
            out.append("<hr />")
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            level = min(len(heading.group(1)) + 1, 6)
            out.append(f"<h{level}>{_inline_markdown(heading.group(2))}</h{level}>")
            continue

        if stripped.startswith("- "):
            out.append(f"<p class='bullet'>• {_inline_markdown(stripped[2:])}</p>")
            continue

        out.append(f"<p>{_inline_markdown(stripped)}</p>")

    flush_table()
    return "\n".join(out)


def _dataframe_to_html(body: Any) -> str:
    try:
        return body.to_html(index=False, border=0, classes="snapshot-table", escape=True)
    except Exception:
        return f"<pre>{html.escape(_safe_str(body), quote=False)}</pre>"


class _ContextProxy:
    def __init__(self, capture: "_StreamlitHtmlCapture", open_html: str = "", close_html: str = "") -> None:
        self.capture = capture
        self.open_html = open_html
        self.close_html = close_html

    def __enter__(self) -> "_StreamlitHtmlCapture":
        if self.open_html:
            self.capture.parts.append(self.open_html)
        return self.capture

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        if self.close_html:
            self.capture.parts.append(self.close_html)
        return False

    def __getattr__(self, name: str) -> Any:
        return getattr(self.capture, name)


class _StreamlitHtmlCapture:
    """Small Streamlit-compatible renderer used only to replay the saved report snapshot.

    The source of truth remains ui.relatorio.render_relatorio_section(calc_snapshot).
    This class only captures the Streamlit calls as printable HTML; it must not create
    a separate simplified summary of the report.
    """

    def __init__(self, session_snapshot: Dict[str, Any] | None = None) -> None:
        self.session_state: Dict[str, Any] = deepcopy(session_snapshot or {})
        self.secrets: Dict[str, Any] = {}
        self.parts: list[str] = []

    def markdown(self, body: Any, *args: Any, **kwargs: Any) -> None:
        self.parts.append(_markdown_to_html(body, allow_raw_html=bool(kwargs.get("unsafe_allow_html"))))

    def subheader(self, body: Any, *args: Any, **kwargs: Any) -> None:
        self.parts.append(f"<h2>{_inline_markdown(body)}</h2>")

    def header(self, body: Any, *args: Any, **kwargs: Any) -> None:
        self.parts.append(f"<h1>{_inline_markdown(body)}</h1>")

    def title(self, body: Any, *args: Any, **kwargs: Any) -> None:
        self.parts.append(f"<h1>{_inline_markdown(body)}</h1>")

    def caption(self, body: Any, *args: Any, **kwargs: Any) -> None:
        self.parts.append(f"<p class='caption'>{_inline_markdown(body)}</p>")

    def info(self, body: Any, *args: Any, **kwargs: Any) -> None:
        self.parts.append(f"<div class='notice info'>{_markdown_to_html(body)}</div>")

    def warning(self, body: Any, *args: Any, **kwargs: Any) -> None:
        self.parts.append(f"<div class='notice warning'>{_markdown_to_html(body)}</div>")

    def error(self, body: Any, *args: Any, **kwargs: Any) -> None:
        self.parts.append(f"<div class='notice error'>{_markdown_to_html(body)}</div>")

    def success(self, body: Any, *args: Any, **kwargs: Any) -> None:
        self.parts.append(f"<div class='notice success'>{_markdown_to_html(body)}</div>")

    def write(self, body: Any, *args: Any, **kwargs: Any) -> None:
        self.parts.append(_markdown_to_html(body))

    def text(self, body: Any, *args: Any, **kwargs: Any) -> None:
        self.parts.append(f"<pre>{html.escape(_safe_str(body), quote=False)}</pre>")

    def table(self, body: Any, *args: Any, **kwargs: Any) -> None:
        self.parts.append(_dataframe_to_html(body))

    def dataframe(self, body: Any, *args: Any, **kwargs: Any) -> None:
        self.table(body, *args, **kwargs)

    def metric(self, label: Any, value: Any, delta: Any = None, *args: Any, **kwargs: Any) -> None:
        delta_html = f"<div class='metric-delta'>{_inline_markdown(delta)}</div>" if delta is not None else ""
        self.parts.append(
            "<div class='snapshot-metric'>"
            f"<div class='metric-label'>{_inline_markdown(label)}</div>"
            f"<div class='metric-value'>{_inline_markdown(value)}</div>"
            f"{delta_html}"
            "</div>"
        )

    def image(self, image: Any, *args: Any, **kwargs: Any) -> None:
        src = _safe_str(image, "")
        caption = _safe_str(kwargs.get("caption"), "")
        if src.startswith("http://") or src.startswith("https://") or src.startswith("data:"):
            self.parts.append(
                "<figure class='snapshot-figure'>"
                f"<img src='{html.escape(src, quote=True)}' />"
                + (f"<figcaption>{_inline_markdown(caption)}</figcaption>" if caption else "")
                + "</figure>"
            )
        else:
            self.parts.append(f"<div class='image-placeholder'>{_inline_markdown(src or caption or 'Imagem')}</div>")

    def json(self, body: Any, *args: Any, **kwargs: Any) -> None:
        try:
            text = json.dumps(body, ensure_ascii=False, indent=2)
        except Exception:
            text = _safe_str(body)
        self.parts.append(f"<pre class='json-block'>{html.escape(text, quote=False)}</pre>")

    def columns(self, spec: Any, *args: Any, **kwargs: Any) -> list[_ContextProxy]:
        count = spec if isinstance(spec, int) else len(spec)
        return [_ContextProxy(self, "<div class='snapshot-column'>", "</div>") for _ in range(count)]

    def expander(self, label: Any, *args: Any, **kwargs: Any) -> _ContextProxy:
        return _ContextProxy(
            self,
            f"<details class='snapshot-expander'><summary>{_inline_markdown(label)}</summary>",
            "</details>",
        )

    def container(self, *args: Any, **kwargs: Any) -> _ContextProxy:
        return _ContextProxy(self, "<section class='snapshot-container'>", "</section>")

    def empty(self, *args: Any, **kwargs: Any) -> _ContextProxy:
        return _ContextProxy(self)

    def divider(self, *args: Any, **kwargs: Any) -> None:
        self.parts.append("<hr />")

    def cache_resource(self, *args: Any, **kwargs: Any) -> Any:
        def decorator(fn: Any) -> Any:
            return fn
        return decorator

    def dump(self) -> str:
        return "\n".join(part for part in self.parts if part)


def _iter_report_modules() -> Iterable[Any]:
    module_names = {
        "ui.relatorio",
        "ui.relatorio_blocks.figuras_anexo_v",
        "ui.relatorio_blocks.quadro_tecnico",
        "ui.relatorio_blocks.shared",
        "ui.relatorio_blocks.unifamiliar",
        "ui.relatorio_blocks.multifamiliar",
        "ui.relatorio_blocks.multifamiliar_guia",
        "ui.relatorio_blocks.unifamiliar_items.common",
        "ui.relatorio_blocks.multifamiliar_items.common",
    }
    for package_name in ("ui.relatorio_blocks", "ui.relatorio_blocks.unifamiliar_items", "ui.relatorio_blocks.multifamiliar_items"):
        try:
            package = importlib.import_module(package_name)
            for info in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
                module_names.add(info.name)
        except Exception:
            continue

    for name in sorted(module_names):
        try:
            yield importlib.import_module(name)
        except Exception:
            continue


@contextmanager
def _patched_streamlit(capture: _StreamlitHtmlCapture):
    patched: list[tuple[Any, str, Any]] = []
    for module in _iter_report_modules():
        if hasattr(module, "st"):
            original = getattr(module, "st")
            setattr(module, "st", capture)
            patched.append((module, "st", original))
    try:
        yield
    finally:
        for module, attr, original in reversed(patched):
            try:
                setattr(module, attr, original)
            except Exception:
                pass


def _render_snapshot_body_html(item: Dict[str, Any]) -> str:
    ctx = item.get("report_context") if isinstance(item.get("report_context"), dict) else {}
    calc = ctx.get("calc_snapshot") if isinstance(ctx.get("calc_snapshot"), dict) else {}
    session_snapshot = ctx.get("session_snapshot") if isinstance(ctx.get("session_snapshot"), dict) else {}
    if not calc:
        raise ValueError("Este relatório salvo ainda não possui calc_snapshot para gerar o snapshot visual.")

    from ui import relatorio

    capture = _StreamlitHtmlCapture(session_snapshot=session_snapshot)
    with _patched_streamlit(capture):
        relatorio.render_relatorio_section(deepcopy(calc))
    return capture.dump()


def build_snapshot_print_html(item: Dict[str, Any]) -> str:
    body = _render_snapshot_body_html(item)
    title = _safe_str(item.get("title") or "Relatório visual do snapshot")
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{html.escape(title)}</title>
<style>
  @page {{ size: A4; margin: 15mm 13mm; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font-family: Arial, Helvetica, sans-serif; color:#162033; background:#ffffff; font-size:11.2pt; line-height:1.45; }}
  main {{ max-width: 980px; margin: 0 auto; padding: 10px 0 24px; }}
  h1, h2, h3, h4 {{ color:#123a66; page-break-after: avoid; line-height:1.22; }}
  h1 {{ font-size:24pt; margin:0 0 14px; }}
  h2 {{ font-size:18pt; margin:18px 0 10px; }}
  h3 {{ font-size:15pt; margin:18px 0 9px; border-top:1px solid #d9e2ef; padding-top:14px; }}
  h4 {{ font-size:12.5pt; margin:12px 0 6px; }}
  p {{ margin: 6px 0; }}
  strong {{ color:#0f2742; }}
  hr {{ border:0; border-top:1px solid #d9e2ef; margin:18px 0 8px; }}
  a {{ color:#155da8; text-decoration:none; }}
  .caption {{ color:#64748b; font-size:9.5pt; }}
  .bullet {{ margin-left: 10px; }}
  .notice {{ border-radius:10px; padding:10px 12px; margin:10px 0; border:1px solid #d8e1ef; background:#f8fafc; }}
  .warning {{ background:#fff8db; border-color:#f1dd8b; }}
  .success {{ background:#eaf8ef; border-color:#bfe7cb; }}
  .error {{ background:#fff1f1; border-color:#f2b8b8; }}
  .snapshot-table {{ width:100%; border-collapse:collapse; margin:8px 0 12px; page-break-inside:auto; }}
  .snapshot-table th, .snapshot-table td {{ border:1px solid #d8e1ef; padding:7px 8px; vertical-align:top; text-align:left; }}
  .snapshot-table th {{ background:#f1f5f9; font-weight:700; color:#123a66; }}
  .snapshot-figure {{ margin: 12px auto 18px; text-align:center; page-break-inside: avoid; }}
  .snapshot-figure img {{ max-width:100%; max-height: 220mm; object-fit: contain; }}
  .snapshot-figure figcaption {{ margin-top:6px; color:#64748b; font-size:9.3pt; }}
  .snapshot-expander {{ border:1px solid #d8e1ef; border-radius:10px; padding:8px 10px; margin:10px 0; }}
  .snapshot-expander summary {{ font-weight:700; color:#123a66; }}
  .snapshot-container {{ margin: 8px 0 12px; }}
  .snapshot-metric {{ border:1px solid #d8e1ef; border-radius:12px; padding:10px 12px; margin:8px 0; background:#f8fafc; }}
  .metric-label {{ color:#64748b; font-size:9.5pt; }}
  .metric-value {{ color:#123a66; font-size:15pt; font-weight:700; }}
  .metric-delta {{ color:#64748b; font-size:9.5pt; }}
  .json-block {{ white-space:pre-wrap; font-size:8.5pt; background:#f8fafc; border:1px solid #d8e1ef; border-radius:8px; padding:8px; }}
  .image-placeholder {{ border:1px dashed #9aa8ba; border-radius:10px; padding:20px; text-align:center; color:#64748b; }}
  @media print {{ main {{ padding:0; }} .snapshot-expander, .snapshot-figure, .snapshot-metric {{ page-break-inside: avoid; }} }}
</style>
</head>
<body>
<main>
{body}
</main>
</body>
</html>"""


def generate_snapshot_html_bytes(item: Dict[str, Any]) -> bytes:
    return build_snapshot_print_html(item).encode("utf-8")


def _external_snapshot_pdf_available() -> bool:
    """Return True when the isolated visual PDF converter is configured.

    The heavy browser-based conversion stays outside the Streamlit app. This keeps
    the main system protected while allowing the Área do Cliente to download the
    same visual PDF already validated on the isolated test page.
    """
    try:
        from core.snapshot_pdf_external import external_converter_available

        return external_converter_available()
    except Exception:
        return False


def _weasyprint_available() -> bool:
    try:
        from weasyprint import HTML  # noqa: F401
        return True
    except Exception:
        return False


def snapshot_pdf_renderer_available() -> bool:
    return _external_snapshot_pdf_available() or _weasyprint_available()


def generate_snapshot_pdf_bytes(item: Dict[str, Any]) -> bytes:
    """Generate a PDF from the real saved report renderer, not from a simplified field summary.

    Preferred path: send the already generated snapshot HTML to the external
    browser-based converter. Fallback: keep the previous WeasyPrint behavior only
    when no external converter URL is configured, preserving compatibility.
    """
    html_doc = build_snapshot_print_html(item)

    if _external_snapshot_pdf_available():
        try:
            from core.snapshot_pdf_external import generate_pdf_from_snapshot_html

            return generate_pdf_from_snapshot_html(html_doc.encode("utf-8"))
        except Exception as exc:
            if exc.__class__.__name__ == "SnapshotPdfExternalUnavailable":
                raise SnapshotPdfUnavailable(str(exc)) from exc
            raise SnapshotPdfUnavailable(
                "Não foi possível gerar o PDF visual pelo conversor externo. "
                "O HTML imprimível foi mantido como alternativa segura."
            ) from exc

    if not _weasyprint_available():
        raise SnapshotPdfUnavailable(
            "PDF visual automático indisponível neste ambiente. Para não gerar um PDF incompleto ou diferente do snapshot, "
            "o sistema disponibiliza o HTML imprimível do snapshot."
        )

    try:
        from weasyprint import HTML

        return HTML(string=html_doc, base_url=os.getcwd()).write_pdf()
    except Exception as exc:
        raise SnapshotPdfUnavailable(
            "Não foi possível converter o snapshot real em PDF neste ambiente. O HTML imprimível foi mantido como alternativa segura."
        ) from exc


def snapshot_file_stem(item: Dict[str, Any]) -> str:
    return f"relatorio_visual_snapshot_{_slug_id(item.get('id'))}"
