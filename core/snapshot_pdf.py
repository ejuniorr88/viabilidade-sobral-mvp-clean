from __future__ import annotations

import html
import json
import os
from datetime import datetime
from typing import Any, Dict, Iterable, List, Tuple
from zoneinfo import ZoneInfo

_TZ = ZoneInfo("America/Fortaleza")


def _safe_str(value: Any, default: str = "—") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _escape(value: Any) -> str:
    return html.escape(_safe_str(value), quote=True)


def _fmt_num(value: Any, decimals: int = 2) -> str:
    try:
        if value is None or value == "":
            return "—"
        number = float(value)
        return f"{number:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return _safe_str(value)


def _fmt_pct(value: Any, decimals: int = 1) -> str:
    try:
        if value is None or value == "":
            return "—"
        return f"{float(value):.{decimals}f}%".replace(".", ",")
    except Exception:
        return _safe_str(value)


def _pick(mapping: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def _rule_pct(rule: Dict[str, Any], key_pct: str, key_frac: str) -> Any:
    value = rule.get(key_pct)
    if value is not None:
        return value
    value = rule.get(key_frac)
    try:
        number = float(value)
        return number * 100 if 0 <= number <= 1 else number
    except Exception:
        return value


def _local_datetime_label(item: Dict[str, Any], ctx: Dict[str, Any]) -> str:
    saved = ctx.get("saved_at_local") or item.get("created_at")
    if saved:
        try:
            raw = str(saved).replace("Z", "+00:00")
            dt = datetime.fromisoformat(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=_TZ)
            else:
                dt = dt.astimezone(_TZ)
            return dt.strftime("%d/%m/%Y às %H:%M")
        except Exception:
            pass
    return _safe_str(ctx.get("saved_at_label") or "—")


def _html_table(rows: Iterable[Tuple[str, Any]]) -> str:
    body = []
    for label, value in rows:
        body.append(f"<tr><th>{_escape(label)}</th><td>{_escape(value)}</td></tr>")
    return "<table>" + "".join(body) + "</table>"


def _parse_rule_src(rule: Dict[str, Any]) -> Dict[str, Any]:
    src = rule.get("src") or {}
    if isinstance(src, str):
        try:
            src = json.loads(src)
        except Exception:
            src = {}
    return src if isinstance(src, dict) else {}


def _extract_figure_number(figure: Dict[str, Any]) -> int | None:
    text = f"{figure.get('title') or figure.get('titulo') or ''} {figure.get('path') or ''}".lower()
    for n in range(1, 8):
        tokens = (f"figura {n}", f"figura_{n}", f"figura-{n}", f"fig {n}", f"fig_{n}", f"fig-{n}", f"/{n}.", f"_{n}.", f"-{n}.")
        if any(token in text for token in tokens):
            return n
    return None


def _public_storage_url(bucket: str, path: str) -> str:
    base = os.getenv("SUPABASE_URL", "").rstrip("/")
    if not base:
        try:
            from core.env_secrets import get_secret_str

            base = get_secret_str("SUPABASE_URL").rstrip("/")
        except Exception:
            base = ""
    if not base:
        return ""
    return f"{base}/storage/v1/object/public/{bucket}/{str(path).lstrip('/')}"


def _figure_blocks(calc: Dict[str, Any], session_snapshot: Dict[str, Any]) -> str:
    rule = calc.get("rule") if isinstance(calc.get("rule"), dict) else {}
    src = _parse_rule_src(rule)
    figures = src.get("figures") or src.get("figuras") or []
    if not isinstance(figures, list):
        return ""

    is_corner = bool(
        session_snapshot.get("lot_is_corner")
        or calc.get("lot_is_corner")
        or calc.get("lote_esquina")
    )
    allowed = {5, 6, 7} if is_corner else {1, 2, 3, 4}
    selected: List[Dict[str, Any]] = []
    for figure in figures:
        if not isinstance(figure, dict):
            continue
        number = _extract_figure_number(figure)
        if number in allowed:
            selected.append(figure)
    if not selected:
        selected = [figure for figure in figures if isinstance(figure, dict)]
    if not selected:
        return ""

    cards = []
    for figure in selected:
        title = _escape(figure.get("title") or figure.get("titulo") or "Figura do Anexo V")
        caption = _escape(figure.get("caption") or figure.get("legenda") or "")
        bucket = _safe_str(figure.get("bucket"), "")
        path = _safe_str(figure.get("path"), "")
        url = _public_storage_url(bucket, path) if bucket and path else ""
        image = f'<img src="{html.escape(url, quote=True)}" alt="{title}" />' if url else f'<div class="image-fallback">{_escape(bucket + "/" + path)}</div>'
        cards.append(f"<div class='figure-card'><h4>{title}</h4>{image}<p>{caption}</p></div>")
    return "<section><h2>Figuras anexas — Anexo V</h2><div class='figure-grid'>" + "".join(cards) + "</div></section>"


def _build_html(item: Dict[str, Any]) -> str:
    ctx = item.get("report_context") if isinstance(item.get("report_context"), dict) else {}
    calc = ctx.get("calc_snapshot") if isinstance(ctx.get("calc_snapshot"), dict) else {}
    session_snapshot = ctx.get("session_snapshot") if isinstance(ctx.get("session_snapshot"), dict) else {}
    inputs = ctx.get("inputs_snapshot") if isinstance(ctx.get("inputs_snapshot"), dict) else {}
    rule = calc.get("rule") if isinstance(calc.get("rule"), dict) else {}

    title = item.get("title") or calc.get("selected_use_label") or calc.get("categoria_label") or "Relatório de Viabilidade Urbanística"
    zone = item.get("zone_label") or calc.get("zone") or calc.get("zone_sigla") or calc.get("zone_label")
    road = item.get("road_name") or calc.get("street_name") or calc.get("road_name") or calc.get("logradouro")
    road_type = item.get("road_type") or calc.get("road_type") or calc.get("via_tipo") or calc.get("street_type")
    status = "Viável" if bool(calc.get("ok")) else "Atenção / condicionado"

    lot_area = _pick(session_snapshot, "lot_area_m2", "area_lote_m2") or calc.get("lot_area_m2")
    built_ground = _pick(inputs, "built_ground_m2") or _pick(session_snapshot, "built_ground_m2", "built_ground_input_m2") or _pick(calc, "built_ground_m2", "built_ground_input_m2")
    permeable = _pick(inputs, "permeable_area_m2") or _pick(session_snapshot, "permeable_area_m2", "area_permeavel_prevista_m2") or _pick(calc, "permeable_area_m2", "area_permeavel_prevista_m2")
    front = _pick(inputs, "lot_front_m") or _pick(session_snapshot, "lot_front_m", "lot_testada_m") or _pick(calc, "lot_front_m", "lot_testada_m")
    depth = _pick(inputs, "lot_depth_m") or _pick(session_snapshot, "lot_depth_m", "lot_profundidade_m") or _pick(calc, "lot_depth_m", "lot_profundidade_m")

    kpi_rows = [
        ("Zona", zone),
        ("Via", road),
        ("Tipo de via", road_type),
        ("Data do relatório", _local_datetime_label(item, ctx)),
    ]
    input_rows = [
        ("Área do lote", f"{_fmt_num(lot_area)} m²"),
        ("Área pretendida no térreo", f"{_fmt_num(built_ground)} m²"),
        ("Área permeável prevista", f"{_fmt_num(permeable)} m²"),
        ("Testada", f"{_fmt_num(front)} m"),
        ("Profundidade", f"{_fmt_num(depth)} m"),
        ("Tipo de lote", "Esquina" if bool(session_snapshot.get("lot_is_corner") or calc.get("lot_is_corner")) else "Meio de quadra"),
    ]
    urban_rows = [
        ("Taxa de permeabilidade mínima", _fmt_pct(_rule_pct(rule, "tp_min_pct", "tp_min"))),
        ("Taxa de ocupação máxima", _fmt_pct(_rule_pct(rule, "to_max_pct", "to_max"))),
        ("TO subsolo", _fmt_pct(_rule_pct(rule, "to_subsolo_max_pct", "to_subsolo"))),
        ("Índice de aproveitamento mínimo", _fmt_num(rule.get("ia_min"), 2)),
        ("Índice de aproveitamento máximo", _fmt_num(rule.get("ia_max"), 2)),
        ("Recuo de frente", f"{_fmt_num(rule.get('recuo_frontal_m'))} m"),
        ("Recuo lateral", f"{_fmt_num(rule.get('recuo_lateral_m'))} m"),
        ("Recuo de fundos", f"{_fmt_num(rule.get('recuo_fundos_m'))} m"),
        ("Altura máxima", f"{_fmt_num(rule.get('gabarito_m'))} m"),
    ]

    notes = []
    for key in ("analysis_summary", "summary", "mensagem", "status_message", "zone_description"):
        value = calc.get(key)
        if value:
            notes.append(f"<p>{_escape(value)}</p>")
    if not notes:
        notes.append("<p>Este PDF visual foi gerado a partir do snapshot salvo do relatório na Área do Cliente. Para interpretação oficial, consulte sempre o órgão competente.</p>")

    figures = _figure_blocks(calc, session_snapshot)

    return f"""
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8" />
<style>
  @page {{ size: A4; margin: 18mm 16mm; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: Arial, Helvetica, sans-serif; color: #172033; font-size: 11.5px; line-height: 1.45; }}
  .cover {{ background: #123A66; color: white; padding: 26px 28px; border-radius: 18px; margin-bottom: 18px; }}
  .brand {{ color: #F59E0B; font-size: 12px; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }}
  h1 {{ font-size: 25px; line-height: 1.16; margin: 8px 0 10px; }}
  h2 {{ color: #123A66; border-bottom: 2px solid #F59E0B; padding-bottom: 6px; margin: 20px 0 10px; font-size: 16px; }}
  h3 {{ color: #123A66; margin: 12px 0 8px; font-size: 13px; }}
  h4 {{ color: #172033; margin: 0 0 8px; font-size: 12px; }}
  .badge {{ display: inline-block; background: #E9F5EF; color: #17633A; border-radius: 999px; padding: 5px 10px; font-weight: 800; }}
  .meta-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 12px 0 0; }}
  .meta-card {{ background: rgba(255,255,255,.10); border: 1px solid rgba(255,255,255,.22); border-radius: 12px; padding: 10px 12px; }}
  .meta-card span {{ display:block; color:#dbe7f3; font-size: 10px; margin-bottom: 3px; }}
  .meta-card strong {{ display:block; color:#fff; font-size: 13px; }}
  section {{ page-break-inside: avoid; }}
  table {{ width: 100%; border-collapse: collapse; margin: 8px 0 14px; }}
  th, td {{ border: 1px solid #E5E7EB; padding: 8px 9px; vertical-align: top; }}
  th {{ width: 42%; background: #F8FAFC; color: #334155; text-align: left; }}
  td {{ color: #111827; }}
  .note {{ background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 12px; padding: 12px 14px; margin-top: 10px; }}
  .figure-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }}
  .figure-card {{ border: 1px solid #E5E7EB; border-radius: 14px; padding: 10px; page-break-inside: avoid; }}
  .figure-card img {{ width: 100%; max-height: 255px; object-fit: contain; border-radius: 10px; background: #F8FAFC; }}
  .figure-card p {{ font-size: 10px; color: #4B5563; margin: 6px 0 0; }}
  .image-fallback {{ background: #F8FAFC; border: 1px dashed #CBD5E1; padding: 18px; border-radius: 10px; color: #64748B; }}
  .footer {{ margin-top: 18px; padding-top: 8px; border-top: 1px solid #E5E7EB; color: #64748B; font-size: 10px; }}
</style>
</head>
<body>
  <div class="cover">
    <div class="brand">Viabilidade Fácil</div>
    <h1>{_escape(title)}</h1>
    <div class="badge">{_escape(status)}</div>
    <div class="meta-grid">
      {''.join(f'<div class="meta-card"><span>{_escape(label)}</span><strong>{_escape(value)}</strong></div>' for label, value in kpi_rows)}
    </div>
  </div>

  <section>
    <h2>Dados do lote e da consulta</h2>
    {_html_table(input_rows)}
  </section>

  <section>
    <h2>Parâmetros urbanísticos do snapshot</h2>
    {_html_table(urban_rows)}
  </section>

  <section>
    <h2>Observações do relatório salvo</h2>
    <div class="note">{''.join(notes)}</div>
  </section>

  {figures}

  <div class="footer">
    Documento visual gerado a partir do snapshot salvo na Área do Cliente. Este material tem caráter orientativo e preliminar e não substitui manifestação oficial do órgão competente.
  </div>
</body>
</html>
"""


def generate_snapshot_pdf_bytes(item: Dict[str, Any]) -> bytes:
    """Gera um PDF visual a partir do report_context salvo em client_reports.

    Esta função é propositalmente independente do Streamlit e do fluxo oficial de geração
    de relatório. Ela usa apenas o snapshot já salvo na Área do Cliente.
    """
    if not isinstance(item, dict):
        raise ValueError("Relatório inválido para gerar PDF visual.")
    ctx = item.get("report_context") if isinstance(item.get("report_context"), dict) else {}
    calc = ctx.get("calc_snapshot") if isinstance(ctx.get("calc_snapshot"), dict) else {}
    if not calc:
        raise ValueError("Este relatório salvo ainda não possui calc_snapshot para gerar PDF visual.")

    try:
        from weasyprint import HTML
    except Exception as exc:  # pragma: no cover - depende do ambiente de deploy
        raise RuntimeError("WeasyPrint não está disponível para gerar o PDF visual do snapshot.") from exc

    html_doc = _build_html(item)
    return HTML(string=html_doc, base_url=os.getcwd()).write_pdf()
