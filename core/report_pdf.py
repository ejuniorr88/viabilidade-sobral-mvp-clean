from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence
from urllib.request import urlopen

from fpdf import FPDF

from ui.relatorio_blocks.dicas_valiosas import get_dicas_valiosas
from ui.relatorio_blocks.figuras_anexo_v import filter_figuras_by_lot_type
from .zone_descriptions import fetch_zone_description

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None


QUADRO_ROWS: List[Dict[str, str]] = [
    {"AMBIENTE": "Sala de estar", "CIRCULO INSCRITO": "2,00 m", "AREA MINIMA": "8,00 m²", "ILUMINACAO": "1/8", "VENTILACAO": "1/12", "PE-DIREITO": "2,50 m", "OBS.": "7"},
    {"AMBIENTE": "Sala de jantar", "CIRCULO INSCRITO": "2,00 m", "AREA MINIMA": "6,00 m²", "ILUMINACAO": "1/8", "VENTILACAO": "1/12", "PE-DIREITO": "2,50 m", "OBS.": "7"},
    {"AMBIENTE": "Cozinha", "CIRCULO INSCRITO": "1,80 m", "AREA MINIMA": "5,00 m²", "ILUMINACAO": "1/8", "VENTILACAO": "1/12", "PE-DIREITO": "2,50 m", "OBS.": "1-7"},
    {"AMBIENTE": "1º e 2º quartos", "CIRCULO INSCRITO": "2,00 m", "AREA MINIMA": "8,00 m²", "ILUMINACAO": "1/8", "VENTILACAO": "1/12", "PE-DIREITO": "2,50 m", "OBS.": "-"},
    {"AMBIENTE": "Demais quartos", "CIRCULO INSCRITO": "2,00 m", "AREA MINIMA": "5,00 m²", "ILUMINACAO": "1/8", "VENTILACAO": "1/12", "PE-DIREITO": "2,50 m", "OBS.": "-"},
    {"AMBIENTE": "Banheiro", "CIRCULO INSCRITO": "1,00 m", "AREA MINIMA": "1,50 m²", "ILUMINACAO": "1/10", "VENTILACAO": "1/16", "PE-DIREITO": "2,20 m", "OBS.": "1-2-3"},
    {"AMBIENTE": "Área de serviço", "CIRCULO INSCRITO": "1,20 m", "AREA MINIMA": "1,80 m²", "ILUMINACAO": "1/10", "VENTILACAO": "1/16", "PE-DIREITO": "2,20 m", "OBS.": "1-2-7"},
    {"AMBIENTE": "Garagem", "CIRCULO INSCRITO": "2,20 m", "AREA MINIMA": "9,00 m²", "ILUMINACAO": "1/14", "VENTILACAO": "1/24", "PE-DIREITO": "2,20 m", "OBS.": "7"},
    {"AMBIENTE": "Escada", "CIRCULO INSCRITO": "0,80 m", "AREA MINIMA": "-", "ILUMINACAO": "-", "VENTILACAO": "-", "PE-DIREITO": "2,10 m", "OBS.": "8-11-12-13"},
]

QUADRO_OBS = [
    "Tolera-se iluminação e ventilação zenital.",
    "Admite-se ventilação mecânica ou indireta nos casos permitidos.",
    "Banheiro não pode comunicar-se diretamente com cozinha ou sala de jantar.",
    "Corredores com mais de 5,00 m devem ter largura mínima de 1,00 m.",
    "Corredores com mais de 10,00 m exigem ventilação mínima proporcional.",
    "Área de porta com veneziana pode ser computada como ventilação.",
    "Escadas devem ser de material incombustível ou tratado.",
    "Patamar obrigatório quando houver mudança de direção ou altura superior a 2,90 m.",
    "Largura mínima do degrau: 0,25 m.",
    "Altura máxima do degrau: 0,19 m.",
]

PERMEABILIDADE_ROWS = [
    ("Grama", "100%"),
    ("Brita solta / terra batida", "100%"),
    ("Piso drenante", "90%"),
    ("Bloco de concreto vazado (piso verde)", "60%"),
    ("Pedra portuguesa / intertravado", "25%"),
]

PORTE_ROWS = [
    ("A", "Adequado / permitido", "Pode seguir com o projeto, respeitando as demais regras."),
    ("I", "Inadequado / não permitido", "Em regra, não pode nesse local/condição."),
    ("AP", "Adequado (pequeno porte)", "Pode, mas normalmente limitado a porte pequeno."),
    ("AM", "Adequado (médio porte)", "Pode, mas normalmente limitado a porte médio."),
    ("AP/AM", "Depende do porte", "Pode, mas depende se o caso é pequeno ou médio."),
    ("PE", "Projeto especial", "Pode exigir análise específica e condições extras no licenciamento."),
]


class _ReportPDF(FPDF):
    def rounded_rect(self, x: float, y: float, w: float, h: float, r: float = 0, style: str = "") -> None:
        rect_fn = getattr(super(), "rounded_rect", None)
        if callable(rect_fn):
            rect_fn(x, y, w, h, r, style=style)
            return
        self.rect(x, y, w, h, style=style)

    def header(self) -> None:
        self.set_fill_color(246, 248, 251)
        self.rect(0, 0, self.w, 18, style="F")
        self.set_y(7)
        self.set_font("Helvetica", "B", 17)
        self.set_text_color(24, 41, 74)
        self.cell(0, 6.5, _sanitize("RELATÓRIO URBANÍSTICO"), new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9.2)
        self.set_text_color(90, 101, 117)
        self.cell(0, 4.5, _sanitize("Viabilidade Fácil / Viabilidade Urbana Sobral"), new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_text_color(0, 0, 0)

    def footer(self) -> None:
        self.set_y(-10)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5, _sanitize(f"Página {self.page_no()}"), align="C")


# ---------- helpers ----------
def _sanitize(text: Any) -> str:
    return str(text).encode("latin-1", "replace").decode("latin-1")


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "sim", "yes", "y"}
    return bool(value)


def _pick_number(*values: Any) -> Optional[float]:
    for value in values:
        parsed = _safe_float(value)
        if parsed is not None:
            return parsed
    return None


def _pick_text(*values: Any, default: str = "-") -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return default


def _fmt_num(value: Any, dec: int = 2) -> str:
    number = _safe_float(value)
    if number is None:
        return "-"
    return f"{number:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_area(value: Any) -> str:
    txt = _fmt_num(value)
    return f"{txt} m²" if txt != "-" else txt


def _fmt_m(value: Any) -> str:
    txt = _fmt_num(value)
    return f"{txt} m" if txt != "-" else txt


def _fmt_pct(value: Any, dec: int = 1) -> str:
    number = _safe_float(value)
    if number is None:
        return "-"
    return f"{number:.{dec}f}%"


def _fmt_int_or_num(value: Any) -> str:
    number = _safe_float(value)
    if number is None:
        return "-"
    if float(number).is_integer():
        return str(int(number))
    return _fmt_num(number)


def _to_pct(rule: Dict[str, Any], key_pct: str, key_frac: str) -> Optional[float]:
    value = _safe_float(rule.get(key_pct))
    if value is not None:
        return value
    value = _safe_float(rule.get(key_frac))
    if value is None:
        return None
    return value * 100.0 if 0 <= value <= 1.0 else value


def _full_width(pdf: _ReportPDF) -> float:
    return max(10.0, pdf.w - pdf.l_margin - pdf.r_margin)


def _ensure_space(pdf: _ReportPDF, needed_h: float) -> None:
    if pdf.get_y() + needed_h > pdf.h - pdf.b_margin:
        pdf.add_page()


def _section_title(pdf: _ReportPDF, number: str, title: str, intro: str = "") -> None:
    _ensure_space(pdf, 16)
    pdf.ln(2)
    y = pdf.get_y()
    pdf.set_fill_color(31, 58, 147)
    pdf.rounded_rect(pdf.l_margin, y, 10, 10, 2, style="F")
    pdf.set_xy(pdf.l_margin, y + 1.8)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(10, 5, _sanitize(number), align="C")
    pdf.set_xy(pdf.l_margin + 14, y + 1)
    pdf.set_text_color(24, 41, 74)
    pdf.set_font("Helvetica", "B", 14)
    pdf.multi_cell(_full_width(pdf) - 14, 5.5, _sanitize(title))
    if intro:
        pdf.set_x(pdf.l_margin + 14)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(70, 77, 90)
        pdf.multi_cell(_full_width(pdf) - 14, 5.2, _sanitize(intro))
    pdf.set_text_color(0, 0, 0)
    pdf.ln(1)


def _paragraph(pdf: _ReportPDF, text: str, *, bold: bool = False, color: tuple[int, int, int] | None = None, h: float = 5.5) -> None:
    _ensure_space(pdf, h + 2)
    pdf.set_font("Helvetica", "B" if bold else "", 10.3)
    if color:
        pdf.set_text_color(*color)
    pdf.multi_cell(_full_width(pdf), h, _sanitize(text))
    pdf.set_text_color(0, 0, 0)


def _bullet_list(pdf: _ReportPDF, items: Sequence[str]) -> None:
    for item in items:
        _ensure_space(pdf, 6.0)
        pdf.set_x(pdf.l_margin + 3)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(_full_width(pdf) - 3, 5.2, _sanitize(f"• {item}"))


def _simple_table(pdf: _ReportPDF, headers: List[str], rows: List[List[str]], widths: List[float], *, font_size: int = 9, line_h: float = 5.4) -> None:
    if not headers or not rows:
        return

    def row_height(row: List[str], font_style: str = "") -> float:
        pdf.set_font("Helvetica", font_style, font_size)
        max_lines = 1
        for idx, text in enumerate(row):
            col_w = max(8.0, widths[idx] - 2.4)
            lines = pdf.multi_cell(col_w, line_h, _sanitize(text), dry_run=True, output="LINES")
            max_lines = max(max_lines, len(lines))
        return max_lines * line_h + 2.0

    header_h = row_height(headers, "B")
    _ensure_space(pdf, header_h + 4)
    x = pdf.l_margin
    y = pdf.get_y()
    pdf.set_fill_color(237, 242, 247)
    pdf.set_draw_color(219, 225, 232)
    pdf.set_font("Helvetica", "B", font_size)
    for idx, head in enumerate(headers):
        w = widths[idx]
        pdf.rect(x, y, w, header_h, style="DF")
        pdf.set_xy(x + 1.2, y + 1)
        pdf.multi_cell(w - 2.4, line_h, _sanitize(head), border=0)
        x += w
    pdf.set_y(y + header_h)

    fill = False
    for row in rows:
        this_h = row_height(row)
        _ensure_space(pdf, this_h + 1)
        x = pdf.l_margin
        y = pdf.get_y()
        pdf.set_fill_color(250, 252, 254 if fill else 255)
        fill = not fill
        pdf.set_font("Helvetica", "", font_size)
        for idx, text in enumerate(row):
            w = widths[idx]
            pdf.rect(x, y, w, this_h, style="DF")
            pdf.set_xy(x + 1.2, y + 1)
            pdf.multi_cell(w - 2.4, line_h, _sanitize(text), border=0)
            x += w
        pdf.set_y(y + this_h)


def _info_box(pdf: _ReportPDF, title: str, text: str, *, tone: str = "neutral") -> None:
    colors = {
        "neutral": ((246, 248, 251), (219, 225, 232), (24, 41, 74)),
        "success": ((240, 253, 244), (187, 247, 208), (22, 101, 52)),
        "warning": ((255, 247, 237), (254, 215, 170), (154, 52, 18)),
    }
    fill, border, title_color = colors.get(tone, colors["neutral"])
    _ensure_space(pdf, 16)
    y = pdf.get_y()
    x = pdf.l_margin
    w = _full_width(pdf)
    pdf.set_fill_color(*fill)
    pdf.set_draw_color(*border)
    pdf.rounded_rect(x, y, w, 14.5, 2, style="DF")
    pdf.set_xy(x + 3, y + 2)
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(*title_color)
    pdf.multi_cell(w - 6, 4.5, _sanitize(title))
    pdf.set_x(x + 3)
    pdf.set_font("Helvetica", "", 9.8)
    pdf.set_text_color(45, 55, 72)
    pdf.multi_cell(w - 6, 4.8, _sanitize(text))
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(max(pdf.get_y(), y + 16.2))


def _formula(pdf: _ReportPDF, text: str) -> None:
    _ensure_space(pdf, 9)
    y = pdf.get_y()
    pdf.set_fill_color(241, 245, 249)
    pdf.set_draw_color(203, 213, 225)
    pdf.rounded_rect(pdf.l_margin, y, _full_width(pdf), 7.8, 1.5, style="DF")
    pdf.set_xy(pdf.l_margin + 3, y + 2)
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 4.0, _sanitize(text))
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(y + 10)


def _kpi_cards(pdf: _ReportPDF, cards: Sequence[tuple[str, str]], cols: int = 3) -> None:
    if not cards:
        return
    gutter = 3.0
    total = _full_width(pdf)
    card_w = (total - gutter * (cols - 1)) / cols
    card_h = 16.5
    row_count = (len(cards) + cols - 1) // cols
    for row_idx in range(row_count):
        chunk = cards[row_idx * cols : (row_idx + 1) * cols]
        _ensure_space(pdf, card_h + 2)
        y = pdf.get_y()
        x = pdf.l_margin
        for label, value in chunk:
            pdf.set_fill_color(248, 250, 252)
            pdf.set_draw_color(226, 232, 240)
            pdf.rounded_rect(x, y, card_w, card_h, 2, style="DF")
            pdf.set_xy(x + 2.5, y + 2)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(100, 116, 139)
            pdf.multi_cell(card_w - 5, 3.6, _sanitize(label))
            pdf.set_xy(x + 2.5, y + 8)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(24, 41, 74)
            pdf.multi_cell(card_w - 5, 4.5, _sanitize(value))
            x += card_w + gutter
        pdf.set_y(y + card_h + 3)
    pdf.set_text_color(0, 0, 0)


def _status_badge(pdf: _ReportPDF, status: str) -> None:
    ok = str(status).strip().upper() == "PERMITE"
    text = _sanitize(status or "-")
    w = 34
    h = 10
    x = pdf.w - pdf.r_margin - w
    y = pdf.get_y()
    pdf.set_fill_color(*(231, 245, 236) if ok else (252, 238, 238))
    pdf.set_draw_color(*(187, 247, 208) if ok else (254, 202, 202))
    pdf.rounded_rect(x, y, w, h, 2, style="DF")
    pdf.set_xy(x, y + 2.1)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*(22, 101, 52) if ok else (153, 52, 52))
    pdf.cell(w, 4.5, text, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(y + h + 2)


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
    figs = src.get("figures") or src.get("figuras") or []
    out: List[Dict[str, Any]] = []
    for item in figs:
        if isinstance(item, dict) and item.get("bucket") and item.get("path"):
            out.append({
                "title": item.get("title") or item.get("titulo") or "Figura",
                "caption": item.get("caption") or item.get("legenda") or "",
                "url": _build_public_storage_url(str(item.get("bucket")), str(item.get("path"))),
            })
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
        return max(1.0, width_px * ratio), max(1.0, height_px * ratio)
    except Exception:
        return max_w, min(max_h, 120.0)


def _extract_context(calc: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
    rule = calc.get("rule") or {}
    area = _pick_number(calc.get("lot_area_m2"), session_state.get("lot_area_m2"), session_state.get("lot_area_input_m2"), calc.get("lot_area_input_m2"))
    front = _pick_number(session_state.get("lot_front_m"), calc.get("lot_front_m"), session_state.get("lot_testada_m"), calc.get("lot_testada_m"), session_state.get("testada_m"), calc.get("testada_m"))
    depth = _pick_number(session_state.get("lot_depth_m"), calc.get("lot_depth_m"), session_state.get("lot_profundidade_m"), calc.get("lot_profundidade_m"), session_state.get("profundidade_m"), calc.get("profundidade_m"))
    built_ground = _pick_number(session_state.get("built_ground_m2"), calc.get("built_ground_m2"), session_state.get("built_ground_input_m2"))
    permeable_area = _pick_number(session_state.get("permeable_area_m2"), session_state.get("area_permeavel_prevista_m2"), calc.get("area_permeavel_prevista_m2"))
    is_corner = _safe_bool(session_state.get("lot_is_corner", calc.get("lot_is_corner", False)))
    is_irregular = _safe_bool(session_state.get("lot_is_irregular", session_state.get("lot_irregular", calc.get("lot_irregular", False))))
    to_max = _to_pct(rule, "to_max_pct", "to_max")
    tp_min = _to_pct(rule, "tp_min_pct", "tp_min")
    ia_max = _pick_number(rule.get("ia_max"), calc.get("ia_max"))
    rec_fr = _pick_number(rule.get("recuo_frontal_m"), 0.0) or 0.0
    rec_lat = _pick_number(rule.get("recuo_lateral_m"), 0.0) or 0.0
    rec_fun = _pick_number(rule.get("recuo_fundos_m"), 0.0) or 0.0
    gabarito = _pick_number(rule.get("gabarito_m"), rule.get("altura_max_m"))
    a_to = area * (to_max / 100.0) if (area is not None and to_max is not None) else None
    a_perm_min = area * (tp_min / 100.0) if (area is not None and tp_min is not None) else None
    a_total = area * ia_max if (area is not None and ia_max is not None) else None
    w_util = (front - 2 * rec_lat) if front is not None else None
    d_util = (depth - rec_fr - rec_fun) if depth is not None else None
    a_recuos = (w_util * d_util) if (w_util is not None and d_util is not None and w_util > 0 and d_util > 0) else None
    a_op1_max = min(a_to, a_recuos) if (a_to is not None and a_recuos is not None) else None
    a_fundo = (front * (depth - rec_fun)) if (front is not None and depth is not None and front > 0 and depth > rec_fun) else None
    a_op2_max = min(a_to, a_fundo) if (a_to is not None and a_fundo is not None) else a_to
    a_adotada = None
    if built_ground is not None and built_ground > 0:
        teto = a_op2_max or a_op1_max or a_to
        a_adotada = min(built_ground, teto) if teto is not None else built_ground

    zone = _pick_text(calc.get("zone"), calc.get("zone_sigla"), rule.get("zone_sigla"))
    via = _pick_text(calc.get("via_nome"), calc.get("street_name"), default="-")
    via_tipo = _pick_text(calc.get("via_tipo"), calc.get("street_type"), default="-")
    uso = _pick_text(calc.get("use_type_code"), default="RES_UNI")
    subzona = _pick_text(rule.get("subzona"), rule.get("subzone_code"), default="PADRAO")
    status_curto = _pick_text(calc.get("status_curto"), calc.get("status_final"), default="PERMITE")
    zona_resultado = _pick_text(calc.get("adequabilidade_zona_desc"), calc.get("adequabilidade_zona"), default="A (Adequado)")
    via_resultado = _pick_text(calc.get("adequabilidade_via_desc"), calc.get("adequabilidade_via"), calc.get("street_result"), default=via_tipo)

    return {
        "rule": rule,
        "area": area,
        "front": front,
        "depth": depth,
        "built_ground": built_ground,
        "permeable_area": permeable_area,
        "is_corner": is_corner,
        "is_irregular": is_irregular,
        "tipo_lote": "Esquina" if is_corner else "Meio de quadra",
        "zone": zone,
        "via": via,
        "via_tipo": via_tipo,
        "uso": uso,
        "subzona": subzona,
        "status_curto": status_curto,
        "zona_resultado": zona_resultado,
        "via_resultado": via_resultado,
        "to_max": to_max,
        "tp_min": tp_min,
        "ia_max": ia_max,
        "rec_fr": rec_fr,
        "rec_lat": rec_lat,
        "rec_fun": rec_fun,
        "gabarito": gabarito,
        "a_to": a_to,
        "a_perm_min": a_perm_min,
        "a_total": a_total,
        "w_util": w_util,
        "d_util": d_util,
        "a_recuos": a_recuos,
        "a_op1_max": a_op1_max,
        "a_op2_max": a_op2_max,
        "a_adotada": a_adotada,
        "zone_description": _fetch_zone_description(_pick_text(calc.get("zone_sigla"), zone), _pick_text(calc.get("subzone_code"), rule.get("subzone_code"), default="PADRAO"), _pick_text(calc.get("zone_label_raw"), zone)),
    }


def _fetch_zone_description(zone_sigla: str, subzone_code: str, zone_label: str = "") -> Optional[Dict[str, Any]]:
    try:
        return fetch_zone_description(zone_sigla or "", subzone_code or "PADRAO", zone_label or zone_sigla or "")
    except Exception:
        return None


def _render_cover(pdf: _ReportPDF, ctx: Dict[str, Any], generated_at: str) -> None:
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(24, 41, 74)
    uso_label = "Residencial Unifamiliar" if str(ctx["uso"]).startswith("RES_UNI") else str(ctx["uso"])
    pdf.multi_cell(_full_width(pdf) - 40, 6.5, _sanitize(uso_label))
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 88, 102)
    pdf.multi_cell(_full_width(pdf) - 40, 5.2, _sanitize(f"Zona {ctx['zone']} | Via: {ctx['via']} | Tipo de lote: {ctx['tipo_lote']} | Emitido em: {generated_at}"))
    pdf.set_y(24)
    _status_badge(pdf, ctx["status_curto"])
    pdf.set_y(40)
    pdf.set_font("Helvetica", "", 10.2)
    pdf.set_text_color(55, 65, 81)
    pdf.multi_cell(_full_width(pdf), 5.4, _sanitize("Este relatório mostra, de forma simples, o que pode ou não pode ser feito no terreno informado, com base na zona, na via e nas regras urbanísticas do município. Primeiro mostramos onde o terreno está, depois se o uso é viável, e em seguida explicamos os principais limites do lote, como ocupação, área livre, altura, vagas, ambientes mínimos e calçada."))
    pdf.ln(2)
    _section_title(pdf, "", "DADOS PRINCIPAIS DO ESTUDO")
    cards = [
        ("ÁREA DO TERRENO", _fmt_area(ctx["area"])),
        ("DIMENSÕES", f"{_fmt_m(ctx['front'])} × {_fmt_m(ctx['depth'])}"),
        ("TIPO DE LOTE", ctx["tipo_lote"]),
        ("SUBZONA / SETOR", ctx["subzona"]),
        ("VIA", ctx["via"]),
        ("TIPO DE VIA", ctx["via_tipo"]),
    ]
    _kpi_cards(pdf, cards, cols=2)


def _render_item_01_localizacao(pdf: _ReportPDF, ctx: Dict[str, Any]) -> None:
    _section_title(pdf, "01", "Onde está localizado o terreno?", "Aqui estão os dados principais usados nesta análise.")
    _kpi_cards(pdf, [
        ("USO INFORMADO", "Residência unifamiliar" if str(ctx["uso"]).startswith("RES_UNI") else ctx["uso"]),
        ("ÁREA DO TERRENO", _fmt_area(ctx["area"])),
        ("DIMENSÕES", f"{_fmt_m(ctx['front'])} × {_fmt_m(ctx['depth'])}"),
        ("ZONA", ctx["zone"]),
        ("SUBZONA / SETOR", ctx["subzona"]),
        ("TIPO DE LOTE", ctx["tipo_lote"]),
        ("VIA", ctx["via"]),
        ("TIPO DE VIA", ctx["via_tipo"]),
    ], cols=2)


def _render_item_02_viabilidade(pdf: _ReportPDF, ctx: Dict[str, Any]) -> None:
    _section_title(pdf, "02", "O uso residencial unifamiliar é viável neste terreno?", "Para o uso residencial unifamiliar, a permissão pode depender principalmente da zona e, em alguns casos, também do tipo da via.")
    _paragraph(pdf, f"Por zona: {ctx['zona_resultado']}")
    _paragraph(pdf, f"Por via: {ctx['via_resultado']}")
    _info_box(pdf, f"Resumo final: {ctx['status_curto']}", "Mesmo quando o resultado for positivo, ainda é necessário cumprir TO, TP, IA, recuos, altura e as demais regras aplicáveis.", tone="success" if str(ctx['status_curto']).upper() == 'PERMITE' else "warning")


def _render_item_03_adequabilidade(pdf: _ReportPDF) -> None:
    _section_title(pdf, "03", "Como funciona a leitura da adequabilidade no unifamiliar?", "No unifamiliar, o resultado não depende só do nome da zona. Em alguns casos, também é preciso observar o tipo da via.")
    _paragraph(pdf, "Pequeno: até 250 m²   |   Médio: 250,01 m² até 1.000 m²   |   Grande: 1.000,01 m² até 5.000 m²")
    _paragraph(pdf, "Projeto especial: acima de 5.000 m²")
    _simple_table(pdf, ["Sigla", "O que significa", "Como interpretar"], [list(r) for r in PORTE_ROWS], [20, 58, 112], font_size=8.8, line_h=5.0)


def _render_item_04_zona(pdf: _ReportPDF, ctx: Dict[str, Any]) -> None:
    desc = ctx.get("zone_description") or {}
    title = _pick_text(desc.get("title"), default=f"{ctx['zone']} — Zona")
    text = _pick_text(desc.get("description_text"), default="Todo terreno está inserido em uma zona, e cada zona pode ter regras, restrições e critérios próprios de uso e ocupação.")
    _section_title(pdf, "04", "O que essa zona permite neste terreno?", "Todo terreno está inserido em uma zona, e cada zona pode ter regras, restrições e critérios próprios de uso e ocupação.")
    _info_box(pdf, title, text)


def _render_item_05_regras(pdf: _ReportPDF, ctx: Dict[str, Any]) -> None:
    _section_title(pdf, "05", "Regras principais para este terreno", "Depois de entender a zona, o próximo passo é ver as regras básicas do lote.")
    _kpi_cards(pdf, [
        ("TO MÁXIMA", _fmt_pct(ctx["to_max"])),
        ("TP MÍNIMA", _fmt_pct(ctx["tp_min"])),
        ("IA MÁXIMO", _fmt_int_or_num(ctx["ia_max"])),
        ("IA MÍNIMO", _pick_text(ctx["rule"].get("ia_min"), default="não informado")),
        ("RECUOS", f"F: {_fmt_m(ctx['rec_fr'])} | L: {_fmt_m(ctx['rec_lat'])} | Fu: {_fmt_m(ctx['rec_fun'])}"),
        ("ALTURA MÁXIMA", _fmt_m(ctx["gabarito"])),
    ], cols=2)


def _render_item_06_07_08(pdf: _ReportPDF, ctx: Dict[str, Any]) -> None:
    area = ctx["area"]
    built_ground = ctx["built_ground"]
    a_adotada = ctx["a_adotada"]
    a_to = ctx["a_to"]
    a_perm_min = ctx["a_perm_min"]

    def tp_scenario(a_terreo: float | None) -> Optional[tuple[float, float]]:
        if a_terreo is None or a_perm_min is None or area is None:
            return None
        a_rest = area - a_terreo
        a_imperm = a_rest - a_perm_min
        return a_rest, a_imperm

    _section_title(pdf, "06", "Quanto posso ocupar no térreo?", "A Taxa de Ocupação mostra o limite percentual permitido para o térreo.")
    if ctx["to_max"] is None or a_to is None:
        _info_box(pdf, "Sem dado cadastrado", "Sem TO máxima cadastrada para esta zona/uso.", tone="warning")
    else:
        _paragraph(pdf, f"A zona permite ocupar até {_fmt_pct(ctx['to_max'])} do terreno no térreo.")
        _formula(pdf, f"{_fmt_area(area)} × {_fmt_pct(ctx['to_max'])} = {_fmt_area(a_to)}")
        _paragraph(pdf, "Esse é o limite máximo permitido pela Taxa de Ocupação (TO).")
        if a_adotada is not None:
            if built_ground is not None and a_adotada < built_ground:
                _info_box(pdf, "Área informada acima do permitido", f"Você informou {_fmt_area(built_ground)} no térreo, mas o máximo permitido é {_fmt_area(a_adotada)}. Os cálculos abaixo usam o valor permitido.", tone="warning")
        if not ctx["is_irregular"]:
            _info_box(pdf, "Opção principal — adotando os recuos da zona", f"Frontal: {_fmt_m(ctx['rec_fr'])} | Laterais: {_fmt_m(ctx['rec_lat'])} cada | Fundo: {_fmt_m(ctx['rec_fun'])}")
            _paragraph(pdf, f"Largura útil: {_fmt_m(ctx['w_util'])} | Profundidade útil: {_fmt_m(ctx['d_util'])}")
            if ctx["a_recuos"] is not None:
                _formula(pdf, f"{_fmt_m(ctx['w_util'])} × {_fmt_m(ctx['d_util'])} = {_fmt_area(ctx['a_recuos'])}")
                _paragraph(pdf, f"Nessa opção, o limite físico pelos recuos é {_fmt_area(ctx['a_op1_max'])}.")
        else:
            _info_box(pdf, "Terreno irregular", "Como o lote não é retangular, o relatório não calcula a implantação por recuos. Aqui são apresentados os limites legais por TO, TP e IA.", tone="warning")
        _info_box(pdf, "Opção alternativa — aproveitando a flexibilidade da lei", "Para residência unifamiliar, a legislação admite zerar o recuo frontal e os recuos laterais, desde que o projeto continue respeitando a TO máxima e a TP mínima.", tone="neutral")
        if ctx["a_op2_max"] is not None:
            _formula(pdf, f"Térreo máximo nesta opção: {_fmt_area(ctx['a_op2_max'])}")

    _section_title(pdf, "07", "Quanto preciso deixar livre?", "Além da ocupação no térreo, a zona exige área permeável mínima.")
    if ctx["tp_min"] is None or a_perm_min is None:
        _info_box(pdf, "Sem dado cadastrado", "Sem TP mínima cadastrada para esta zona/uso.", tone="warning")
    else:
        _paragraph(pdf, f"A zona exige {_fmt_pct(ctx['tp_min'])} de área permeável.")
        _formula(pdf, f"{_fmt_area(area)} × {_fmt_pct(ctx['tp_min'])} = {_fmt_area(a_perm_min)} obrigatórios permeáveis")
        tp2 = tp_scenario(ctx["a_op2_max"])
        if tp2:
            a_rest, a_imperm = tp2
            _info_box(pdf, "Cenário pela opção principal", f"Usando {_fmt_area(ctx['a_op2_max'])} no térreo, sobra {_fmt_area(a_rest)} no lote. Desses, {_fmt_area(a_perm_min)} devem permitir infiltração no solo e {_fmt_area(a_imperm)} podem receber piso impermeável.")
        if a_adotada is not None:
            tpu = tp_scenario(a_adotada)
            if tpu and ctx["a_op2_max"] != a_adotada:
                a_rest, a_imperm = tpu
                _info_box(pdf, "Cenário com a área adotada do projeto", f"Usando {_fmt_area(a_adotada)} no térreo, sobra {_fmt_area(a_rest)} no lote. Desses, {_fmt_area(a_perm_min)} devem permitir infiltração no solo e {_fmt_area(a_imperm)} podem receber piso impermeável.")

    _section_title(pdf, "08", "Tipos de piso: o que conta como permeável?", "Nem todo piso externo conta do mesmo jeito na permeabilidade.")
    _simple_table(pdf, ["Tipo de piso", "Percentual considerado permeável"], [[a, b] for a, b in PERMEABILIDADE_ROWS], [120, 60], font_size=9)
    _paragraph(pdf, "Isso ajuda a entender que nem toda área “livre” do lote conta 100% como permeável.")


def _render_item_09_10(pdf: _ReportPDF, ctx: Dict[str, Any]) -> None:
    _section_title(pdf, "09", "Posso construir mais andares?", "Além da ocupação no térreo, a zona também define o potencial construtivo total do lote por meio do Índice de Aproveitamento (IA).")
    if ctx["ia_max"] is None or ctx["a_total"] is None:
        _info_box(pdf, "Sem dado cadastrado", "Sem IA máximo cadastrado para esta zona/uso.", tone="warning")
    else:
        _formula(pdf, f"{_fmt_area(ctx['area'])} × {_fmt_num(ctx['ia_max'])} = {_fmt_area(ctx['a_total'])}")
        _paragraph(pdf, f"Esse é o total que pode ser distribuído entre térreo e pavimentos superiores, respeitando também os demais parâmetros urbanísticos.")
        if ctx["gabarito"] is not None:
            _info_box(pdf, "Altura máxima da zona", _fmt_m(ctx["gabarito"]))
            _paragraph(pdf, "Exemplo simples: adotando pé-direito médio de 3,00 m por pavimento, isso pode permitir algo próximo de 5 pavimentos, apenas como referência inicial.")

    _section_title(pdf, "10", "Preciso de vagas de estacionamento?", "A exigência de vagas depende do tipo de uso previsto na legislação.")
    _info_box(pdf, "Estacionamento", "Neste caso, não existe exigência mínima obrigatória de vagas de estacionamento. Essa exigência costuma aparecer em residências multifamiliares e em outras atividades previstas na lei.")


def _render_item_11_quadro(pdf: _ReportPDF) -> None:
    _section_title(pdf, "11", "Quais medidas mínimas os ambientes precisam ter?", "Além das regras do lote, a legislação também traz medidas mínimas para alguns ambientes da edificação.")
    headers = ["Ambiente", "Círculo inscrito", "Área mínima", "Iluminação", "Ventilação", "Pé-direito", "Obs."]
    rows = [[row["AMBIENTE"], row["CIRCULO INSCRITO"], row["AREA MINIMA"], row["ILUMINACAO"], row["VENTILACAO"], row["PE-DIREITO"], row["OBS."]] for row in QUADRO_ROWS]
    _simple_table(pdf, headers, rows, [44, 28, 26, 22, 22, 23, 15], font_size=8.4, line_h=4.9)
    pdf.ln(2)
    _info_box(pdf, "Observações aplicáveis", "\n".join(f"• {obs}" for obs in QUADRO_OBS))


def _render_item_12_calcada(pdf: _ReportPDF) -> None:
    _section_title(pdf, "12", "O que preciso saber sobre a calçada?", "A análise não termina dentro do lote. Também existem regras para calçada, acesso ao imóvel, rebaixo de meio-fio e relação do lote com a rua.")


def _render_item_13_dicas(pdf: _ReportPDF, is_corner: bool = False) -> None:
    _section_title(pdf, "13", "Dicas valiosas")
    for item in get_dicas_valiosas(is_corner=is_corner):
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            titulo = str(item[0] or "").strip()
            texto = str(item[1] or "").strip()
            _info_box(pdf, titulo or "Dica", texto)
        else:
            texto = str(item or "").strip()
            if texto:
                _info_box(pdf, "Dica", texto)


def _render_item_14_resumo(pdf: _ReportPDF, ctx: Dict[str, Any]) -> None:
    _section_title(pdf, "14", "Resumo rápido final")
    title = _pick_text((ctx.get("zone_description") or {}).get("title"), default=ctx["zone"])
    _paragraph(pdf, title, bold=True)
    _kpi_cards(pdf, [
        ("ZONA", ctx["zone"]),
        ("TO MÁXIMA", _fmt_pct(ctx["to_max"])),
        ("TP MÍNIMA", _fmt_pct(ctx["tp_min"])),
        ("IA MÁXIMO", _fmt_int_or_num(ctx["ia_max"])),
        ("ALTURA MÁXIMA", _fmt_m(ctx["gabarito"])),
        ("ÁREA MÁXIMA NO TÉRREO", _fmt_area(ctx["a_op2_max"] or ctx["a_to"])),
        ("ÁREA PERMEÁVEL MÍNIMA", _fmt_area(ctx["a_perm_min"])),
        ("ÁREA TOTAL MÁXIMA", _fmt_area(ctx["a_total"])),
    ], cols=2)
    _paragraph(pdf, "Em resumo: você pode ocupar até a TO máxima da zona no térreo, precisa manter a TP mínima do terreno permeável, pode construir até o IA máximo no total e deve respeitar os limites de altura, recuos e demais exigências urbanísticas.")


def _render_item_15_documentos(pdf: _ReportPDF) -> None:
    simplificado = [
        "Documento de identidade do requerente ou representante legal",
        "CPF ou CNPJ",
        "Matrícula atualizada do imóvel ou documento equivalente",
        "Certidão negativa de IPTU",
        "Parecer favorável de Adequabilidade Locacional",
        "Tabela com índices urbanísticos e áreas da edificação",
        "Projeto arquitetônico em arquivo digital",
        "ART/RRT do responsável técnico",
        "Termo de responsabilidade do responsável técnico",
        "Termo de responsabilidade do proprietário",
        "Isenção da licença ambiental",
    ]
    obra_nova = [
        "Requerimento único",
        "Documento de identidade do requerente ou representante legal",
        "CPF ou CNPJ",
        "Matrícula atualizada do imóvel",
        "Autorização do proprietário, quando necessária",
        "BCI",
        "ART/RRT com comprovante de pagamento",
        "Projeto arquitetônico assinado",
        "Projeto hidrossanitário",
        "Memorial de cálculo e drenagem pluvial",
        "Declaração do SAAE sobre rede de esgoto, quando necessária",
        "Aprovação do Corpo de Bombeiros, IPHAN, licenciamento ambiental, PGRSCC, COMAR, DNIT/SOP ou EIV, quando aplicável",
    ]
    _section_title(pdf, "15", "O que acontece depois desta etapa?", "Após a finalização dos projetos, será necessário dar entrada na documentação junto à Prefeitura para obter o alvará de construção.")
    _info_box(pdf, "Alvará de Construção Simplificado", "\n".join(f"• {item}" for item in simplificado))
    _info_box(pdf, "Alvará de Construção (Obra Nova)", "\n".join(f"• {item}" for item in obra_nova))


def _render_item_16_fechamento(pdf: _ReportPDF) -> None:
    _section_title(pdf, "16", "Fechamento final")
    _paragraph(pdf, "Este relatório foi pensado para ajudar a entender o terreno de forma mais simples. Na etapa de projeto e aprovação, ainda será preciso conferir os detalhes completos no setor de licenciamento de obras da Prefeitura.")
    pdf.set_font("Helvetica", "I", 8.5)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(_full_width(pdf), 4.4, _sanitize("Documento gerado pelo Viabilidade Fácil com base no mesmo conteúdo exibido na tela do relatório urbanístico."))
    pdf.set_text_color(0, 0, 0)


def _render_figuras(pdf: _ReportPDF, figures: List[Dict[str, Any]]) -> None:
    if not figures:
        return
    temp_files: List[str] = []
    try:
        for index, figure in enumerate(figures, start=1):
            title = _pick_text(figure.get("title"), default=f"Figura {index}")
            caption = _pick_text(figure.get("caption"), default="")
            url = figure.get("url")
            pdf.add_page()
            _section_title(pdf, f"{12 + index:02d}", title, caption if caption and caption != title else "Anexo V – LC 90/2023")
            if not url:
                _info_box(pdf, "Figura indisponível", "Figura sem URL pública disponível.", tone="warning")
                continue
            temp = _download_temp_image(url)
            if not temp:
                _info_box(pdf, "Falha ao carregar figura", "Não foi possível carregar esta figura no PDF.", tone="warning")
                continue
            temp_files.append(temp)
            max_w = _full_width(pdf)
            max_h = pdf.h - pdf.get_y() - pdf.b_margin - 10
            img_w, img_h = _fit_image_size(temp, max_w, max_h)
            try:
                x = pdf.l_margin + ((_full_width(pdf) - img_w) / 2)
                y = pdf.get_y()
                pdf.image(temp, x=x, y=y, w=img_w, h=img_h)
                pdf.set_y(y + img_h + 3)
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(110, 110, 110)
                pdf.multi_cell(_full_width(pdf), 4.5, _sanitize("Anexo V - LC 90/2023"), align="C")
                pdf.set_text_color(0, 0, 0)
            except Exception:
                _info_box(pdf, "Falha ao renderizar figura", "Não foi possível renderizar esta figura no PDF.", tone="warning")
    finally:
        for path in temp_files:
            try:
                os.remove(path)
            except Exception:
                pass


def build_report_payload(calc: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
    rule = calc.get("rule") or {}
    return {
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "calc": calc,
        "session_state": session_state,
        "figures": filter_figuras_by_lot_type(_extract_figures_from_rule(rule), is_corner=bool(session_state.get("lot_is_corner") or calc.get("lot_is_corner"))),
    }


def generate_report_pdf_bytes(calc: Dict[str, Any], session_state: Dict[str, Any]) -> bytes:
    payload = build_report_payload(calc, session_state)
    ctx = _extract_context(calc, session_state)
    pdf = _ReportPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.set_margins(14, 24, 14)
    pdf.add_page()

    _render_cover(pdf, ctx, payload["generated_at"])
    _render_item_01_localizacao(pdf, ctx)
    _render_item_02_viabilidade(pdf, ctx)
    _render_item_03_adequabilidade(pdf)
    _render_item_04_zona(pdf, ctx)
    _render_item_05_regras(pdf, ctx)
    _render_item_06_07_08(pdf, ctx)
    _render_item_09_10(pdf, ctx)
    _render_item_11_quadro(pdf)
    _render_item_12_calcada(pdf)
    _render_figuras(pdf, payload.get("figures", []))
    _render_item_13_dicas(pdf, is_corner=bool(ctx["is_corner"]))
    _render_item_14_resumo(pdf, ctx)
    _render_item_15_documentos(pdf)
    _render_item_16_fechamento(pdf)

    result = pdf.output(dest="S")
    if isinstance(result, bytearray):
        return bytes(result)
    if isinstance(result, bytes):
        return result
    return result.encode("latin-1", errors="replace")
