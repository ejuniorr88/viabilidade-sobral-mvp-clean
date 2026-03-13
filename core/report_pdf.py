from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.request import urlopen

from fpdf import FPDF

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None


def _safe_str(value: Any, default: str = "—") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _fmt_num(value: Any, dec: int = 2, suffix: str = "") -> str:
    number = _safe_float(value)
    if number is None:
        return "—"
    text = f"{number:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{text}{suffix}"


def _fmt_pct(value: Any, dec: int = 1) -> str:
    number = _safe_float(value)
    if number is None:
        return "—"
    return f"{number:.{dec}f}%"


def _to_pct(rule: Dict[str, Any], key_pct: str, key_frac: str) -> Optional[float]:
    value = rule.get(key_pct)
    if value is not None:
        return _safe_float(value)

    value = rule.get(key_frac)
    if value is None:
        return None

    parsed = _safe_float(value)
    if parsed is None:
        return None

    return parsed * 100.0 if 0 <= parsed <= 1.0 else parsed


def _sanitize(text: str) -> str:
    return text.encode("latin-1", "replace").decode("latin-1")


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

    path = path.lstrip("/")
    return f"{base}/storage/v1/object/public/{bucket}/{path}"


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

    figs = src.get("figures") or src.get("figuras") or []
    if not isinstance(figs, list):
        return []

    out: List[Dict[str, Any]] = []
    for item in figs:
        if isinstance(item, dict) and item.get("bucket") and item.get("path"):
            url = _build_public_storage_url(str(item.get("bucket")), str(item.get("path")))
            out.append(
                {
                    "title": item.get("title") or item.get("titulo") or "Figura",
                    "caption": item.get("caption") or item.get("legenda") or "",
                    "url": url,
                }
            )
    return out


def _download_temp_image(url: str) -> Optional[str]:
    try:
        with urlopen(url, timeout=15) as resp:
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




def _short_ref(text: Any, limit: int = 90) -> str:
    value = _safe_str(text, "")
    if not value:
        return ""
    value = value.replace("\n", " ").replace("\r", " ").strip()
    if len(value) <= limit:
        return value
    head = max(20, limit // 2 - 2)
    tail = max(12, limit - head - 3)
    return f"{value[:head]}...{value[-tail:]}"


def _fit_image_size(path: str, max_w: float, max_h: float) -> tuple[float, float]:
    if max_w <= 0 or max_h <= 0:
        return max(1.0, max_w), max(1.0, max_h)

    if Image is None:
        return max_w, min(max_h, 120.0)

    try:
        with Image.open(path) as img:
            width_px, height_px = img.size
        if width_px <= 0 or height_px <= 0:
            return max_w, min(max_h, 120.0)

        ratio = min(max_w / width_px, max_h / height_px)
        if ratio <= 0:
            return max_w, min(max_h, 120.0)
        return width_px * ratio, height_px * ratio
    except Exception:
        return max_w, min(max_h, 120.0)

def _build_rows(calc: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
    rule = calc.get("rule") or {}
    zone = calc.get("zone") or calc.get("zone_sigla") or "—"
    via = calc.get("via_nome") or calc.get("street_name") or "—"
    via_tipo = calc.get("via_tipo") or calc.get("street_type") or "—"
    uso = calc.get("use_type_code") or "—"

    lot_area = _safe_float(calc.get("lot_area_m2") or session_state.get("lot_area_m2"))
    built_ground = _safe_float(session_state.get("built_ground_m2"))
    permeable_area = _safe_float(session_state.get("permeable_area_m2"))
    front = _safe_float(session_state.get("lot_front_m"))
    depth = _safe_float(session_state.get("lot_depth_m"))
    is_corner = bool(session_state.get("lot_is_corner"))
    is_irregular = bool(session_state.get("lot_is_irregular"))

    to_max = _to_pct(rule, "to_max_pct", "to_max")
    tp_min = _to_pct(rule, "tp_min_pct", "tp_min")
    ia_max = rule.get("ia_max")

    identification = [
        ("Zona", _safe_str(zone)),
        ("Via", _safe_str(via)),
        ("Tipo de via", _safe_str(via_tipo)),
        ("Uso analisado", _safe_str(uso)),
        ("Tipo de lote", "Esquina" if is_corner else "Meio de quadra"),
        ("Terreno irregular", "Sim" if is_irregular else "Não"),
        ("Área do terreno", _fmt_num(lot_area, suffix=" m²")),
        ("Frente do lote", _fmt_num(front, suffix=" m")),
        ("Profundidade do lote", _fmt_num(depth, suffix=" m")),
    ]

    parameters = [
        ("TO máxima", _fmt_pct(to_max)),
        ("TP mínima", _fmt_pct(tp_min)),
        ("IA máximo", _fmt_num(ia_max)),
        ("Recuo frontal", _fmt_num(rule.get("recuo_frontal_m"), suffix=" m")),
        ("Recuo lateral", _fmt_num(rule.get("recuo_lateral_m"), suffix=" m")),
        ("Recuo fundos", _fmt_num(rule.get("recuo_fundos_m"), suffix=" m")),
        ("Gabarito", _fmt_num(rule.get("gabarito_m"), suffix=" m")),
    ]

    calculations = [
        ("Área térrea informada", _fmt_num(built_ground, suffix=" m²")),
        ("Área permeável informada", _fmt_num(permeable_area, suffix=" m²")),
        ("Taxa de ocupação calculada", _fmt_pct(calc.get("to_pct"))),
        ("Taxa de permeabilidade calculada", _fmt_pct(calc.get("tp_pct"))),
        ("Índice de aproveitamento calculado", _fmt_num(calc.get("ia"))),
        ("Adequabilidade final", _safe_str(calc.get("adequabilidade_txt") or calc.get("adequability_result"))),
    ]

    environment_table = [
        ("Área do terreno", _fmt_num(lot_area, suffix=" m²")),
        ("Área térrea considerada", _fmt_num(built_ground, suffix=" m²")),
        ("Área permeável considerada", _fmt_num(permeable_area, suffix=" m²")),
        ("Frente", _fmt_num(front, suffix=" m")),
        ("Profundidade", _fmt_num(depth, suffix=" m")),
        ("TO máxima da zona", _fmt_pct(to_max)),
        ("TP mínima da zona", _fmt_pct(tp_min)),
        ("IA máximo da zona", _fmt_num(ia_max)),
        ("Recuo frontal", _fmt_num(rule.get("recuo_frontal_m"), suffix=" m")),
        ("Recuo lateral", _fmt_num(rule.get("recuo_lateral_m"), suffix=" m")),
        ("Recuo fundos", _fmt_num(rule.get("recuo_fundos_m"), suffix=" m")),
        ("Gabarito", _fmt_num(rule.get("gabarito_m"), suffix=" m")),
    ]

    notes: List[tuple[str, str]] = []

    if calc.get("err"):
        notes.append(("Observação", _safe_str(calc.get("err"))))

    if is_irregular:
        notes.append(
            (
                "Lote irregular",
                "Como o lote é irregular, a implantação final pode ser reduzida por recuos, forma do lote, alinhamento, servidões e exigências do licenciamento.",
            )
        )

    notes.append(
        (
            "Passeios (calçadas)",
            "Não há, na legislação municipal, uma medida única e fixa para a largura dos passeios. Quando existir, deve-se adotar o padrão definido no projeto aprovado do loteamento e/ou nas diretrizes urbanísticas da via. Na ausência dessa previsão, utiliza-se como referência o passeio já implantado no logradouro, garantindo continuidade e alinhamento.",
        )
    )
    notes.append(
        (
            "Piscinas",
            "Piscinas não entram na área construída para TO, mas contam como área impermeável para TP e devem respeitar afastamento mínimo de 0,50 m das divisas.",
        )
    )

    figures = _extract_figures_from_rule(rule)

    return {
        "identification": identification,
        "parameters": parameters,
        "calculations": calculations,
        "environment_table": environment_table,
        "notes": notes,
        "figures": figures,
    }


def build_report_payload(calc: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
    rows = _build_rows(calc, session_state)
    return {
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "title": "Relatório Urbanístico",
        "sections": rows,
    }


class _ReportPDF(FPDF):
    def header(self) -> None:
        self.set_fill_color(31, 42, 68)
        self.rect(0, 0, 210, 22, style="F")
        self.set_xy(14, 6)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 8, _sanitize("Viabilidade Fácil"), ln=True)
        self.set_x(14)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, _sanitize("Relatório Urbanístico"), ln=True)
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


def _section_title(pdf: _ReportPDF, title: str) -> None:
    pdf.ln(2)
    pdf.set_fill_color(238, 242, 247)
    pdf.set_draw_color(225, 230, 236)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(31, 42, 68)
    pdf.cell(0, 8, _sanitize(title), ln=True, fill=True, border=1)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(1)


def _row(pdf: _ReportPDF, label: str, value: str) -> None:
    page_w = pdf.w - pdf.l_margin - pdf.r_margin
    label_w = 58
    value_w = page_w - label_w - 2

    x = pdf.get_x()
    y = pdf.get_y()

    pdf.set_font("Helvetica", "B", 10)
    pdf.multi_cell(label_w, 6, _sanitize(f"{label}:"), border=0)
    label_end_y = pdf.get_y()

    pdf.set_xy(x + label_w + 2, y)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(value_w, 6, _sanitize(value), border=0)
    value_end_y = pdf.get_y()

    pdf.set_y(max(label_end_y, value_end_y) + 0.5)


def _render_section(pdf: _ReportPDF, title: str, rows: List[tuple[str, str]]) -> None:
    _section_title(pdf, title)
    for label, value in rows:
        _row(pdf, label, value)


def _render_highlight_box(pdf: _ReportPDF, title: str, body: str) -> None:
    pdf.set_fill_color(250, 251, 253)
    pdf.set_draw_color(220, 226, 234)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, _sanitize(title), ln=True, fill=True, border=1)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5.5, _sanitize(body), border=1, fill=False)
    pdf.ln(1)


def _render_environment_table(pdf: _ReportPDF, rows: List[tuple[str, str]]) -> None:
    _section_title(pdf, "4. QUADRO TÉCNICO – PARÂMETROS DOS AMBIENTES")

    page_w = pdf.w - pdf.l_margin - pdf.r_margin
    col1 = 110
    col2 = page_w - col1

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(245, 247, 250)
    pdf.cell(col1, 8, _sanitize("Parâmetro"), border=1, fill=True)
    pdf.cell(col2, 8, _sanitize("Valor"), border=1, fill=True, ln=True)

    pdf.set_font("Helvetica", "", 10)
    for label, value in rows:
        x = pdf.get_x()
        y = pdf.get_y()

        pdf.multi_cell(col1, 7, _sanitize(label), border=1)
        left_end_y = pdf.get_y()

        pdf.set_xy(x + col1, y)
        pdf.multi_cell(col2, 7, _sanitize(value), border=1)
        right_end_y = pdf.get_y()

        pdf.set_y(max(left_end_y, right_end_y))


def _render_figures(pdf: _ReportPDF, figures: List[Dict[str, Any]]) -> None:
    if not figures:
        return

    _section_title(pdf, "5. Figuras anexas (Anexo V)")

    temp_files: List[str] = []

    try:
        for fig in figures:
            title = _safe_str(fig.get("title"), "Figura")
            caption = _safe_str(fig.get("caption"), "")
            url = fig.get("url")

            pdf.add_page()
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(0, 6, _sanitize(title))

            if caption and caption != "—":
                pdf.set_x(pdf.l_margin)
                pdf.set_font("Helvetica", "", 9)
                pdf.multi_cell(0, 5, _sanitize(caption))
                pdf.ln(2)

            if url:
                tmp_path = _download_temp_image(url)
                if tmp_path:
                    temp_files.append(tmp_path)
                    try:
                        current_y = pdf.get_y()
                        usable_w = pdf.w - pdf.l_margin - pdf.r_margin
                        usable_h = pdf.h - pdf.b_margin - current_y
                        if usable_h < 60:
                            pdf.add_page()
                            current_y = pdf.get_y()
                            usable_h = pdf.h - pdf.b_margin - current_y

                        img_w, img_h = _fit_image_size(tmp_path, usable_w, max(40.0, usable_h - 2.0))
                        pdf.image(tmp_path, x=pdf.l_margin, y=current_y, w=img_w, h=img_h)
                        pdf.set_y(current_y + img_h + 4)
                    except Exception:
                        pdf.set_x(pdf.l_margin)
                        pdf.set_font("Helvetica", "", 9)
                        pdf.multi_cell(0, 5, _sanitize("Não foi possível renderizar esta figura no PDF. A geração do relatório continuará sem interromper o restante do documento."))
                        ref = _short_ref(url)
                        if ref:
                            pdf.set_x(pdf.l_margin)
                            pdf.set_font("Helvetica", "I", 8)
                            pdf.multi_cell(0, 4.5, _sanitize(f"Referência da figura: {ref}"))
                else:
                    pdf.set_x(pdf.l_margin)
                    pdf.set_font("Helvetica", "", 9)
                    pdf.multi_cell(0, 5, _sanitize("Não foi possível baixar esta figura para o PDF."))
                    ref = _short_ref(url)
                    if ref:
                        pdf.set_x(pdf.l_margin)
                        pdf.set_font("Helvetica", "I", 8)
                        pdf.multi_cell(0, 4.5, _sanitize(f"Referência da figura: {ref}"))
            else:
                pdf.set_x(pdf.l_margin)
                pdf.set_font("Helvetica", "", 9)
                pdf.multi_cell(0, 5, _sanitize("Figura sem URL pública disponível."))

            pdf.ln(2)
    finally:
        for path in temp_files:
            try:
                os.remove(path)
            except Exception:
                pass


def generate_report_pdf_bytes(calc: Dict[str, Any], session_state: Dict[str, Any]) -> bytes:
    payload = build_report_payload(calc, session_state)
    sections: Dict[str, Any] = payload["sections"]

    pdf = _ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_margins(14, 28, 14)
    pdf.add_page()

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 6, _sanitize(f"Emitido em: {payload['generated_at']}"), ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    _render_highlight_box(
        pdf,
        "Resumo",
        "Este relatório apresenta a leitura inicial da viabilidade urbanística do lote analisado, com identificação da zona, parâmetros urbanísticos, síntese da análise, quadro técnico e observações importantes para apoiar o início do projeto.",
    )

    _render_section(pdf, "1. Identificação da análise", sections["identification"])
    _render_section(pdf, "2. Parâmetros urbanísticos", sections["parameters"])
    _render_section(pdf, "3. Síntese da análise", sections["calculations"])
    _render_environment_table(pdf, sections["environment_table"])
    _render_section(pdf, "4. Dicas e observações importantes", sections["notes"])
    _render_figures(pdf, sections.get("figures", []))

    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(110, 110, 110)
    pdf.multi_cell(
        0,
        4.5,
        _sanitize(
            "Documento gerado pelo Viabilidade Fácil. O PDF foi estruturado para se aproximar da leitura do sistema e já permite evolução futura para histórico na área do cliente."
        ),
    )
    pdf.set_text_color(0, 0, 0)

    result = pdf.output(dest="S")
    if isinstance(result, bytearray):
        return bytes(result)
    if isinstance(result, bytes):
        return result
    return result.encode("latin-1", errors="replace")
