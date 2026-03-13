from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.request import urlopen

from fpdf import FPDF

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None


# =============================
# Helpers
# =============================

def _safe_str(value: Any, default: str = "—") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None


def _fmt_num(value: Any, dec: int = 2, suffix: str = "") -> str:
    n = _safe_float(value)
    if n is None:
        return "—"
    text = f"{n:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{text}{suffix}"


def _fmt_pct(value: Any, dec: int = 1) -> str:
    n = _safe_float(value)
    if n is None:
        return "—"
    return f"{n:.{dec}f}%"


def _to_pct(rule: Dict[str, Any], key_pct: str, key_frac: str) -> Optional[float]:
    value = rule.get(key_pct)
    if value is not None:
        return _safe_float(value)
    value = rule.get(key_frac)
    parsed = _safe_float(value)
    if parsed is None:
        return None
    return parsed * 100.0 if 0 <= parsed <= 1 else parsed


def _sanitize(text: Any) -> str:
    return _safe_str(text, "").encode("latin-1", "replace").decode("latin-1")


def _short_ref(text: Any, limit: int = 70) -> str:
    value = _safe_str(text, "")
    if not value:
        return ""
    value = value.replace("\n", " ").replace("\r", " ").strip()
    if len(value) <= limit:
        return value
    head = max(18, limit // 2 - 2)
    tail = max(10, limit - head - 3)
    return f"{value[:head]}...{value[-tail:]}"


def _build_public_storage_url(bucket: str, path: str) -> Optional[str]:
    base = os.getenv("SUPABASE_URL", "").rstrip("/")
    if not base:
        try:
            import streamlit as st
            base = (st.secrets.get("SUPABASE_URL") or "").rstrip("/")
        except Exception:
            base = ""

    if not base or not bucket or not path:
        return None
    return f"{base}/storage/v1/object/public/{bucket}/{path.lstrip('/')}"


def _extract_figures_from_rule(rule: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(rule, dict):
        return []

    src = rule.get("src") or {}
    if isinstance(src, str):
        try:
            src = json.loads(src)
        except Exception:
            src = {}

    if not isinstance(src, dict):
        return []

    figures = src.get("figures") or src.get("figuras") or []
    out: List[Dict[str, Any]] = []
    for item in figures if isinstance(figures, list) else []:
        if not isinstance(item, dict):
            continue
        bucket = item.get("bucket")
        path = item.get("path")
        if not bucket or not path:
            continue
        out.append(
            {
                "title": item.get("title") or item.get("titulo") or "Figura",
                "caption": item.get("caption") or item.get("legenda") or "",
                "url": _build_public_storage_url(str(bucket), str(path)),
                "path": str(path),
            }
        )
    return out


def _download_temp_image(url: str) -> Optional[str]:
    try:
        with urlopen(url, timeout=20) as resp:
            data = resp.read()
        suffix = ".png"
        lower = url.lower()
        if ".jpg" in lower or ".jpeg" in lower:
            suffix = ".jpg"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(data)
        tmp.flush()
        tmp.close()
        return tmp.name
    except Exception:
        return None


def _fit_image_size(path: str, max_w: float, max_h: float) -> Tuple[float, float]:
    max_w = max(1.0, max_w)
    max_h = max(1.0, max_h)
    if Image is None:
        return max_w, min(max_h, 160.0)
    try:
        with Image.open(path) as img:
            width_px, height_px = img.size
        if width_px <= 0 or height_px <= 0:
            return max_w, min(max_h, 160.0)
        ratio = min(max_w / width_px, max_h / height_px)
        return width_px * ratio, height_px * ratio
    except Exception:
        return max_w, min(max_h, 160.0)


def _build_rows(calc: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
    rule = calc.get("rule") or {}

    lot_area = _safe_float(calc.get("lot_area_m2") or session_state.get("lot_area_m2"))
    built_ground = _safe_float(session_state.get("built_ground_m2") or calc.get("built_ground_m2"))
    permeable_area = _safe_float(session_state.get("permeable_area_m2") or calc.get("permeable_area_m2"))
    front = _safe_float(session_state.get("lot_front_m") or calc.get("lot_front_m") or calc.get("front_m"))
    depth = _safe_float(session_state.get("lot_depth_m") or calc.get("lot_depth_m") or calc.get("depth_m"))
    is_corner = bool(session_state.get("lot_is_corner") or calc.get("lot_is_corner"))
    is_irregular = bool(session_state.get("lot_is_irregular") or calc.get("lot_is_irregular"))

    zone = calc.get("zone") or calc.get("zone_sigla") or rule.get("zone_sigla") or "—"
    via = calc.get("via_nome") or calc.get("street_name") or "—"
    via_tipo = calc.get("via_tipo") or calc.get("street_type") or "—"
    uso = calc.get("use_type_code") or calc.get("use_code") or "—"

    to_max = _to_pct(rule, "to_max_pct", "to_max")
    tp_min = _to_pct(rule, "tp_min_pct", "tp_min")
    ia_max = rule.get("ia_max")
    ia_min = rule.get("ia_min")

    identification = [
        ("Uso analisado", _safe_str(uso)),
        ("Zona", _safe_str(zone)),
        ("Rua / Logradouro", _safe_str(via)),
        ("Tipo de via", _safe_str(via_tipo)),
        ("Tipo de lote", "Esquina" if is_corner else "Meio de quadra"),
        ("Terreno irregular", "Sim" if is_irregular else "Não"),
        ("Área do terreno", _fmt_num(lot_area, suffix=" m²")),
        ("Testada / Frente", _fmt_num(front, suffix=" m")),
        ("Profundidade / Lateral", _fmt_num(depth, suffix=" m")),
    ]

    parameters = [
        ("TP mínima", _fmt_pct(tp_min)),
        ("TO máxima", _fmt_pct(to_max)),
        ("TO do subsolo máxima", _fmt_pct(_to_pct(rule, "to_subsolo_max_pct", "to_subsolo_max"))),
        ("IA máximo", _fmt_num(ia_max)),
        ("IA mínimo", _fmt_num(ia_min)),
        ("Recuo frontal", _fmt_num(rule.get("recuo_frontal_m"), suffix=" m")),
        ("Recuo lateral", _fmt_num(rule.get("recuo_lateral_m"), suffix=" m")),
        ("Recuo de fundo", _fmt_num(rule.get("recuo_fundos_m"), suffix=" m")),
        ("Área mínima do lote", _fmt_num(rule.get("area_min_lote_m2"), suffix=" m²")),
        ("Área máxima do lote", _fmt_num(rule.get("area_max_lote_m2"), suffix=" m²")),
        ("Testada mínima", _safe_str(rule.get("testada_min_txt") or rule.get("testada_min_m") or "—")),
        ("Testada máxima", _fmt_num(rule.get("testada_max_m"), suffix=" m")),
        ("Altura máxima", _fmt_num(rule.get("gabarito_m"), suffix=" m")),
        ("Subzona", _safe_str(rule.get("subzone_code") or rule.get("subzona") or "—")),
    ]

    calculations = [
        ("TO utilizada", _fmt_pct(calc.get("to_pct"))),
        ("TP prevista", _fmt_pct(calc.get("tp_pct"))),
        ("IA utilizado", _fmt_num(calc.get("ia"))),
        ("Adequabilidade final", _safe_str(calc.get("adequabilidade_txt") or calc.get("adequability_result") or "—")),
    ]

    notes: List[Tuple[str, str]] = []
    if calc.get("err"):
        notes.append(("Observação", _safe_str(calc.get("err"))))
    if is_irregular:
        notes.append((
            "Lote irregular",
            "Como o lote é irregular, a implantação final pode ser reduzida pela forma do lote, recuos, alinhamento, servidões e demais exigências do licenciamento.",
        ))

    notes.append((
        "Passeios (calçadas)",
        "Não há, na legislação municipal, uma medida única e fixa para a largura dos passeios. Quando existir, deve-se adotar o padrão definido no projeto aprovado do loteamento e/ou nas diretrizes urbanísticas da via; na ausência dessa previsão, utiliza-se como referência o passeio já implantado no logradouro, garantindo continuidade e alinhamento.",
    ))
    notes.append((
        "Piscinas",
        "Se for construída uma piscina, ela não é computada como área construída e, por isso, não entra no cálculo da Taxa de Ocupação (TO). Porém, para a Taxa de Permeabilidade (TP), a piscina é considerada área impermeável, reduzindo a área permeável do lote. Além disso, deve manter afastamento mínimo de 0,50 m das divisas.",
    ))

    figures = _extract_figures_from_rule(rule)

    return {
        "identification": identification,
        "parameters": parameters,
        "calculations": calculations,
        "notes": notes,
        "figures": figures,
    }


# =============================
# PDF
# =============================
class _ReportPDF(FPDF):
    def header(self) -> None:
        self.set_fill_color(31, 42, 68)
        self.rect(0, 0, 210, 22, style="F")
        self.set_xy(14, 6)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 8, _sanitize("Viabilidade Fácil"), new_x="LMARGIN", new_y="NEXT")
        self.set_x(14)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, _sanitize("Relatório Urbanístico"), new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(6)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_draw_color(220, 220, 220)
        self.line(14, self.get_y(), 196, self.get_y())
        self.set_y(-10)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(90, 90, 90)
        self.cell(0, 6, _sanitize(f"Página {self.page_no()}"), align="C")
        self.set_text_color(0, 0, 0)


def _full_w(pdf: _ReportPDF) -> float:
    return pdf.w - pdf.l_margin - pdf.r_margin


def _ensure_left(pdf: _ReportPDF) -> None:
    if pdf.get_x() > (pdf.w - pdf.r_margin - 20):
        pdf.set_x(pdf.l_margin)


def _mc(pdf: _ReportPDF, text: Any, h: float = 5.5, align: str = "L") -> None:
    _ensure_left(pdf)
    w = pdf.w - pdf.r_margin - pdf.get_x()
    if w < 25:
        pdf.set_x(pdf.l_margin)
        w = _full_w(pdf)
    pdf.multi_cell(w, h, _sanitize(text), align=align)


def _section_title(pdf: _ReportPDF, title: str) -> None:
    pdf.ln(2)
    pdf.set_x(pdf.l_margin)
    pdf.set_fill_color(238, 242, 247)
    pdf.set_draw_color(225, 230, 236)
    pdf.set_text_color(31, 42, 68)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(_full_w(pdf), 8, _sanitize(title), border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(1)


def _row(pdf: _ReportPDF, label: str, value: str) -> None:
    pdf.set_x(pdf.l_margin)
    label_w = 58
    value_w = max(40.0, _full_w(pdf) - label_w - 2)
    x = pdf.get_x()
    y = pdf.get_y()

    pdf.set_font("Helvetica", "B", 10)
    pdf.multi_cell(label_w, 6, _sanitize(f"{label}:"), border=0)
    y1 = pdf.get_y()

    pdf.set_xy(x + label_w + 2, y)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(value_w, 6, _sanitize(value), border=0)
    y2 = pdf.get_y()

    pdf.set_xy(pdf.l_margin, max(y1, y2) + 0.5)


def _render_kv_section(pdf: _ReportPDF, title: str, rows: List[Tuple[str, str]]) -> None:
    if not rows:
        return
    _section_title(pdf, title)
    for label, value in rows:
        _row(pdf, label, value)


def _render_highlight_box(pdf: _ReportPDF, title: str, body: str) -> None:
    pdf.set_x(pdf.l_margin)
    pdf.set_fill_color(250, 251, 253)
    pdf.set_draw_color(220, 226, 234)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(_full_w(pdf), 7, _sanitize(title), border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(_full_w(pdf), 5.5, _sanitize(body), border=1)
    pdf.ln(1)


def _render_notes(pdf: _ReportPDF, rows: List[Tuple[str, str]]) -> None:
    if not rows:
        return
    _section_title(pdf, "4. Dicas e observações importantes")
    for label, value in rows:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B", 10)
        _mc(pdf, label, 6)
        pdf.set_font("Helvetica", "", 9.5)
        _mc(pdf, value, 5.4)
        pdf.ln(1)


def _render_figures(pdf: _ReportPDF, figures: List[Dict[str, Any]]) -> None:
    if not figures:
        return

    _section_title(pdf, "5. Figuras anexas (Anexo V)")
    temp_files: List[str] = []

    try:
        for idx, fig in enumerate(figures, start=1):
            title = _safe_str(fig.get("title"), f"Figura {idx}")
            caption = _safe_str(fig.get("caption"), "")
            path_ref = _short_ref(fig.get("path") or fig.get("url"))
            url = fig.get("url")

            pdf.add_page()
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(_full_w(pdf), 6.5, _sanitize(title))

            if caption and caption != "—":
                pdf.set_x(pdf.l_margin)
                pdf.set_font("Helvetica", "", 9.5)
                pdf.multi_cell(_full_w(pdf), 5.2, _sanitize(caption))
                pdf.ln(1)

            if not url:
                pdf.set_x(pdf.l_margin)
                pdf.set_font("Helvetica", "", 9)
                pdf.multi_cell(_full_w(pdf), 5, _sanitize("Figura sem URL pública disponível."))
                continue

            tmp_path = _download_temp_image(url)
            if not tmp_path:
                pdf.set_x(pdf.l_margin)
                pdf.set_font("Helvetica", "", 9)
                pdf.multi_cell(_full_w(pdf), 5, _sanitize("Não foi possível baixar esta figura para o PDF."))
                if path_ref:
                    pdf.set_x(pdf.l_margin)
                    pdf.set_font("Helvetica", "I", 8)
                    pdf.multi_cell(_full_w(pdf), 4.2, _sanitize(f"Arquivo: {path_ref}"))
                continue

            temp_files.append(tmp_path)
            try:
                current_y = pdf.get_y()
                max_w = _full_w(pdf)
                max_h = pdf.h - pdf.b_margin - current_y - 2
                if max_h < 60:
                    pdf.add_page()
                    current_y = pdf.get_y()
                    max_h = pdf.h - pdf.b_margin - current_y - 2

                img_w, img_h = _fit_image_size(tmp_path, max_w, max_h)
                x = pdf.l_margin + max(0.0, (max_w - img_w) / 2)
                pdf.image(tmp_path, x=x, y=current_y, w=img_w, h=img_h)
                pdf.set_xy(pdf.l_margin, current_y + img_h + 3)

                if path_ref:
                    pdf.set_font("Helvetica", "I", 8)
                    pdf.set_text_color(120, 120, 120)
                    pdf.multi_cell(_full_w(pdf), 4.2, _sanitize(f"Arquivo: {path_ref}"))
                    pdf.set_text_color(0, 0, 0)
            except Exception:
                pdf.set_xy(pdf.l_margin, pdf.get_y())
                pdf.set_font("Helvetica", "", 9)
                pdf.multi_cell(_full_w(pdf), 5, _sanitize("Não foi possível renderizar esta figura no PDF. A geração continuará sem interromper o restante do documento."))
                if path_ref:
                    pdf.set_font("Helvetica", "I", 8)
                    pdf.multi_cell(_full_w(pdf), 4.2, _sanitize(f"Arquivo: {path_ref}"))
    finally:
        for path in temp_files:
            try:
                os.remove(path)
            except Exception:
                pass


def build_report_payload(calc: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "title": "Relatório Urbanístico",
        "sections": _build_rows(calc, session_state),
    }


def generate_report_pdf_bytes(calc: Dict[str, Any], session_state: Dict[str, Any]) -> bytes:
    payload = build_report_payload(calc, session_state)
    sections = payload["sections"]

    pdf = _ReportPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_margins(14, 28, 14)
    pdf.add_page()

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 90, 90)
    pdf.set_x(pdf.l_margin)
    pdf.cell(_full_w(pdf), 6, _sanitize(f"Emitido em: {payload['generated_at']}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    _render_highlight_box(
        pdf,
        "Resumo",
        "Este relatório apresenta a leitura inicial da viabilidade urbanística do lote analisado, com identificação da zona, parâmetros urbanísticos, síntese da análise, observações importantes e figuras anexas para apoiar o início do projeto.",
    )

    _render_kv_section(pdf, "1. Identificação da análise", sections.get("identification", []))
    _render_kv_section(pdf, "2. Parâmetros urbanísticos", sections.get("parameters", []))
    _render_kv_section(pdf, "3. Síntese da análise", sections.get("calculations", []))
    _render_notes(pdf, sections.get("notes", []))
    _render_figures(pdf, sections.get("figures", []))

    pdf.ln(2)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(110, 110, 110)
    pdf.multi_cell(
        _full_w(pdf),
        4.5,
        _sanitize("Documento gerado pelo Viabilidade Fácil. Esta versão prioriza estabilidade de geração e preservação das informações do relatório."),
    )
    pdf.set_text_color(0, 0, 0)

    result = pdf.output(dest="S")
    if isinstance(result, bytearray):
        return bytes(result)
    if isinstance(result, bytes):
        return result
    return result.encode("latin-1", errors="replace")
