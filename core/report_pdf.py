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
    {"Ambiente": "Sala de estar", "Círculo inscrito": "2,00 m", "Área mínima": "8,00 m²", "Iluminação": "1/8", "Ventilação": "1/12", "Pé-direito": "2,50 m", "Obs.": "7"},
    {"Ambiente": "Sala de jantar", "Círculo inscrito": "2,00 m", "Área mínima": "6,00 m²", "Iluminação": "1/8", "Ventilação": "1/12", "Pé-direito": "2,50 m", "Obs.": "7"},
    {"Ambiente": "Cozinha", "Círculo inscrito": "1,80 m", "Área mínima": "5,00 m²", "Iluminação": "1/8", "Ventilação": "1/12", "Pé-direito": "2,50 m", "Obs.": "1-7"},
    {"Ambiente": "1º e 2º quartos", "Círculo inscrito": "2,00 m", "Área mínima": "8,00 m²", "Iluminação": "1/8", "Ventilação": "1/12", "Pé-direito": "2,50 m", "Obs.": "-"},
    {"Ambiente": "Demais quartos", "Círculo inscrito": "2,00 m", "Área mínima": "5,00 m²", "Iluminação": "1/8", "Ventilação": "1/12", "Pé-direito": "2,50 m", "Obs.": "-"},
    {"Ambiente": "Banheiro", "Círculo inscrito": "1,00 m", "Área mínima": "1,50 m²", "Iluminação": "1/10", "Ventilação": "1/16", "Pé-direito": "2,20 m", "Obs.": "1-2-3"},
    {"Ambiente": "Área de serviço", "Círculo inscrito": "1,20 m", "Área mínima": "1,80 m²", "Iluminação": "1/10", "Ventilação": "1/16", "Pé-direito": "2,20 m", "Obs.": "1-2-7"},
    {"Ambiente": "Garagem", "Círculo inscrito": "2,20 m", "Área mínima": "9,00 m²", "Iluminação": "1/14", "Ventilação": "1/24", "Pé-direito": "2,20 m", "Obs.": "7"},
    {"Ambiente": "Escada", "Círculo inscrito": "0,80 m", "Área mínima": "-", "Iluminação": "-", "Ventilação": "-", "Pé-direito": "2,10 m", "Obs.": "8-11-12-13"},
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


class ReportPDF(FPDF):
    def rounded_rect(self, x: float, y: float, w: float, h: float, r: float = 0, style: str = "") -> None:
        rect_fn = getattr(super(), "rounded_rect", None)
        if callable(rect_fn):
            rect_fn(x, y, w, h, r, style=style)
            return
        self.rect(x, y, w, h, style=style)

    def header(self) -> None:
        self.set_fill_color(243, 246, 250)
        self.rect(0, 0, self.w, 18, style="F")
        self.set_xy(self.l_margin, 6)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(29, 44, 78)
        self.cell(0, 6, san("RELATÓRIO URBANÍSTICO"))
        self.set_xy(self.l_margin, 12)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(90, 99, 115)
        self.cell(0, 4, san("Viabilidade Fácil / Viabilidade Urbana Sobral"))
        self.set_y(22)

    def footer(self) -> None:
        self.set_y(-9)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 4, san(f"Página {self.page_no()}"), align="C")


def san(text: Any) -> str:
    return str(text).encode("latin-1", "replace").decode("latin-1")


def safe_float(v: Any) -> Optional[float]:
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None


def safe_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in {"1", "true", "yes", "sim"}
    return bool(v)


def pick_number(*values: Any) -> Optional[float]:
    for v in values:
        n = safe_float(v)
        if n is not None:
            return n
    return None


def pick_text(*values: Any, default: str = "-") -> str:
    for v in values:
        if v is None:
            continue
        s = str(v).strip()
        if s:
            return s
    return default


def fmt_num(v: Any, dec: int = 2) -> str:
    n = safe_float(v)
    if n is None:
        return "-"
    return f"{n:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(v: Any, dec: int = 1) -> str:
    n = safe_float(v)
    if n is None:
        return "-"
    return f"{n:.{dec}f}%"


def fmt_area(v: Any) -> str:
    s = fmt_num(v)
    return f"{s} m²" if s != "-" else s


def fmt_m(v: Any) -> str:
    s = fmt_num(v)
    return f"{s} m" if s != "-" else s


def fmt_plain(v: Any) -> str:
    n = safe_float(v)
    if n is None:
        return "-"
    if float(n).is_integer():
        return str(int(n))
    return fmt_num(n)


def full_w(pdf: ReportPDF) -> float:
    return pdf.w - pdf.l_margin - pdf.r_margin


def ensure_space(pdf: ReportPDF, h: float) -> None:
    if pdf.get_y() + h > pdf.h - pdf.b_margin:
        pdf.add_page()


def section_title(pdf: ReportPDF, n: str, title: str) -> None:
    ensure_space(pdf, 12)
    pdf.ln(2)
    x = pdf.l_margin
    y = pdf.get_y()
    pdf.set_fill_color(32, 77, 156)
    pdf.rect(x, y, 12, 8, style="F")
    pdf.set_xy(x, y + 1.6)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(12, 4, san(n), align="C")
    pdf.set_xy(x + 15, y + 0.6)
    pdf.set_text_color(35, 46, 68)
    pdf.set_font("Helvetica", "B", 13)
    pdf.multi_cell(full_w(pdf) - 15, 6, san(title))
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(y + 10)


def paragraph(pdf: ReportPDF, text: str, *, bold: bool = False, color: tuple[int, int, int] | None = None, h: float = 5.2) -> None:
    ensure_space(pdf, h + 1)
    pdf.set_font("Helvetica", "B" if bold else "", 10)
    if color:
        pdf.set_text_color(*color)
    pdf.multi_cell(full_w(pdf), h, san(text))
    pdf.set_text_color(0, 0, 0)


def bullet_list(pdf: ReportPDF, items: Sequence[str]) -> None:
    for it in items:
        ensure_space(pdf, 5.8)
        pdf.set_x(pdf.l_margin + 2)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(full_w(pdf) - 2, 5.2, san(f"• {it}"))


def card_box(pdf: ReportPDF, title: str, body_lines: Sequence[str], *, fill=(248,250,252), title_color=(29,44,78)) -> None:
    line_h = 4.9
    body_h = max(1, len(body_lines)) * line_h
    h = 7 + body_h + 3
    ensure_space(pdf, h + 2)
    x = pdf.l_margin
    y = pdf.get_y()
    pdf.set_fill_color(*fill)
    pdf.set_draw_color(224, 228, 234)
    pdf.rounded_rect(x, y, full_w(pdf), h, 1.8, style="DF")
    pdf.set_xy(x + 3, y + 2.5)
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(*title_color)
    pdf.cell(0, 4, san(title))
    pdf.set_xy(x + 3, y + 7.5)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    for line in body_lines:
        pdf.multi_cell(full_w(pdf) - 6, line_h, san(line))
        pdf.set_x(x + 3)
    pdf.set_y(y + h + 2)


def kpi_row(pdf: ReportPDF, items: Sequence[tuple[str, str]], widths: Sequence[float]) -> None:
    assert len(items) == len(widths)
    ensure_space(pdf, 15)
    x = pdf.l_margin
    y = pdf.get_y()
    for (label, value), w in zip(items, widths):
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(224, 228, 234)
        pdf.rounded_rect(x, y, w, 13.5, 1.5, style="DF")
        pdf.set_xy(x + 2, y + 2)
        pdf.set_font("Helvetica", "B", 8.2)
        pdf.set_text_color(95, 95, 95)
        pdf.multi_cell(w - 4, 3.2, san(label))
        pdf.set_xy(x + 2, y + 7.2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(24, 41, 74)
        pdf.multi_cell(w - 4, 4.2, san(value), align="L")
        x += w + 2.5
    pdf.set_text_color(0,0,0)
    pdf.set_y(y + 16)


def simple_table(pdf: ReportPDF, headers: List[str], rows: List[List[str]], widths: List[float], *, font_size: int = 9, line_h: float = 5.0) -> None:
    def row_h(row: List[str], bold=False):
        pdf.set_font("Helvetica", "B" if bold else "", font_size)
        max_lines = 1
        for idx, txt in enumerate(row):
            lines = pdf.multi_cell(max(4, widths[idx]-2), line_h, san(txt), dry_run=True, output="LINES")
            max_lines = max(max_lines, len(lines))
        return max_lines * line_h + 2

    hh = row_h(headers, True)
    ensure_space(pdf, hh+2)
    x = pdf.l_margin
    y = pdf.get_y()
    pdf.set_fill_color(235, 241, 250)
    pdf.set_draw_color(220,224,230)
    pdf.set_font("Helvetica", "B", font_size)
    for head, w in zip(headers, widths):
        pdf.rect(x, y, w, hh, style="DF")
        pdf.set_xy(x+1, y+1)
        pdf.multi_cell(w-2, line_h, san(head))
        x += w
    pdf.set_y(y+hh)
    flip = False
    for row in rows:
        rh = row_h(row)
        ensure_space(pdf, rh+1)
        x = pdf.l_margin
        y = pdf.get_y()
        pdf.set_fill_color(*( (255,255,255) if not flip else (250,252,255) ))
        flip = not flip
        pdf.set_font("Helvetica", "", font_size)
        for txt, w in zip(row, widths):
            pdf.rect(x, y, w, rh, style="DF")
            pdf.set_xy(x+1, y+1)
            pdf.multi_cell(w-2, line_h, san(txt))
            x += w
        pdf.set_y(y+rh)


def status_badge(pdf: ReportPDF, text: str) -> None:
    x = pdf.l_margin
    y = pdf.get_y()
    w = 35
    pdf.set_fill_color(231,245,236)
    pdf.set_draw_color(187,247,208)
    pdf.rounded_rect(x, y, w, 9, 1.4, style="DF")
    pdf.set_xy(x, y+2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(27,112,61)
    pdf.cell(w, 4, san(text), align="C")
    pdf.set_text_color(0,0,0)


def build_public_storage_url(bucket: str, path: str) -> Optional[str]:
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


def extract_figures_from_rule(rule: Dict[str, Any]) -> List[Dict[str, Any]]:
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
                "url": build_public_storage_url(str(item.get("bucket")), str(item.get("path"))),
            })
    return out


def download_temp_image(url: str) -> Optional[str]:
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


def fit_image_size(path: str, max_w: float, max_h: float) -> tuple[float, float]:
    if Image is None:
        return max_w, min(max_h, 120)
    try:
        with Image.open(path) as img:
            w_px, h_px = img.size
        ratio = min(max_w / w_px, max_h / h_px)
        return max(1.0, w_px * ratio), max(1.0, h_px * ratio)
    except Exception:
        return max_w, min(max_h, 120)


def _to_pct(rule: Dict[str, Any], key_pct: str, key_frac: str) -> Optional[float]:
    value = safe_float(rule.get(key_pct))
    if value is not None:
        return value
    value = safe_float(rule.get(key_frac))
    if value is None:
        return None
    return value * 100.0 if 0 <= value <= 1.0 else value


def fetch_zone_desc(zone_sigla: str, subzone_code: str, zone_label: str = "") -> Optional[Dict[str, Any]]:
    try:
        return fetch_zone_description(zone_sigla or "", subzone_code or "PADRAO", zone_label or zone_sigla or "")
    except Exception:
        return None


def extract_context(calc: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
    rule = calc.get("rule") or {}
    area = pick_number(calc.get("lot_area_m2"), session_state.get("lot_area_m2"), session_state.get("lot_area_input_m2"), calc.get("lot_area_input_m2"))
    front = pick_number(session_state.get("lot_front_m"), calc.get("lot_front_m"), session_state.get("lot_testada_m"), calc.get("lot_testada_m"), session_state.get("testada_m"), calc.get("testada_m"))
    depth = pick_number(session_state.get("lot_depth_m"), calc.get("lot_depth_m"), session_state.get("lot_profundidade_m"), calc.get("lot_profundidade_m"), session_state.get("profundidade_m"), calc.get("profundidade_m"))
    built_ground = pick_number(session_state.get("built_ground_m2"), calc.get("built_ground_m2"), session_state.get("built_ground_input_m2"))
    permeable_area = pick_number(session_state.get("permeable_area_m2"), session_state.get("area_permeavel_prevista_m2"), calc.get("area_permeavel_prevista_m2"))
    is_corner = safe_bool(session_state.get("lot_is_corner", calc.get("lot_is_corner", False)))
    is_irregular = safe_bool(session_state.get("lot_is_irregular", session_state.get("lot_irregular", calc.get("lot_irregular", False))))

    to_max = _to_pct(rule, "to_max_pct", "to_max")
    tp_min = _to_pct(rule, "tp_min_pct", "tp_min")
    ia_max = pick_number(rule.get("ia_max"), calc.get("ia_max"))
    ia_min = pick_number(rule.get("ia_min"), calc.get("ia_min"))
    rec_fr = pick_number(rule.get("recuo_frontal_m"), 0.0) or 0.0
    rec_lat = pick_number(rule.get("recuo_lateral_m"), 0.0) or 0.0
    rec_fun = pick_number(rule.get("recuo_fundos_m"), 0.0) or 0.0
    gabarito = pick_number(rule.get("gabarito_m"), rule.get("altura_max_m"))

    a_to = area * (to_max / 100.0) if (area is not None and to_max is not None) else None
    a_perm_min = area * (tp_min / 100.0) if (area is not None and tp_min is not None) else None
    a_total = area * ia_max if (area is not None and ia_max is not None) else None
    w_util = (front - 2 * rec_lat) if front is not None else None
    d_util = (depth - rec_fr - rec_fun) if depth is not None else None
    a_recuos = (w_util * d_util) if (w_util is not None and d_util is not None and w_util > 0 and d_util > 0) else None
    a_op1_max = min(a_to, a_recuos) if (a_to is not None and a_recuos is not None) else None
    a_fundo = (front * (depth - rec_fun)) if (front is not None and depth is not None and front > 0 and depth > rec_fun) else None
    a_op2_max = min(a_to, a_fundo) if (a_to is not None and a_fundo is not None) else a_to
    a_teto_projeto = a_op2_max or a_op1_max or a_to
    area_pedida = built_ground if built_ground is not None and built_ground > 0 else None
    excedeu_area = False
    a_considerada = None
    if area_pedida is not None:
        if a_teto_projeto is not None:
            a_considerada = min(area_pedida, a_teto_projeto)
            excedeu_area = area_pedida > a_teto_projeto + 1e-9
        else:
            a_considerada = area_pedida
    tp_user = None
    a_livre = None
    a_imperm_poss = None
    to_projeto_pct = None
    a_ia_saldo = None
    if a_considerada is not None and area not in (None, 0):
        to_projeto_pct = (a_considerada / area) * 100.0
        a_livre = area - a_considerada
        if a_perm_min is not None:
            a_imperm_poss = a_livre - a_perm_min
        if a_total is not None:
            a_ia_saldo = a_total - a_considerada
        if a_livre is not None:
            tp_user = (a_livre / area) * 100.0
    tipo_lote = "Esquina" if is_corner else "Meio de quadra"
    zone = pick_text(calc.get("zone"), calc.get("zone_sigla"), rule.get("zone_sigla"))
    via = pick_text(calc.get("via_nome"), calc.get("street_name"), default="-")
    via_tipo = pick_text(calc.get("via_tipo"), calc.get("street_type"), default="-")
    uso = pick_text(calc.get("use_type_code"), default="RES_UNI")
    uso_label = "Residência unifamiliar" if uso.startswith("RES_UNI") else uso
    subzona = pick_text(rule.get("subzona"), rule.get("subzone_code"), calc.get("subzone_code"), default="PADRAO")
    status_curto = pick_text(calc.get("status_curto"), calc.get("resultado_final"), default="SEM DADO")
    icon = pick_text(calc.get("icon"), default="")
    explicacao = pick_text(calc.get("explicacao"), default="")
    zone_class = pick_text(calc.get("zone_class"), default="")
    via_class = pick_text(calc.get("via_class"), default="")
    via_norm = pick_text(calc.get("via_norm"), default="")
    zone_title = zone
    desc = fetch_zone_desc(pick_text(calc.get("zone_sigla"), zone), pick_text(calc.get("subzone_code"), subzona), pick_text(calc.get("zone_label_raw"), zone))
    if desc and desc.get("title"):
        zone_title = str(desc.get("title"))
    return {
        "rule": rule,
        "area": area, "front": front, "depth": depth,
        "built_ground": built_ground, "permeable_area": permeable_area,
        "is_corner": is_corner, "is_irregular": is_irregular, "tipo_lote": tipo_lote,
        "zone": zone, "via": via, "via_tipo": via_tipo, "uso": uso, "uso_label": uso_label,
        "subzona": subzona, "to_max": to_max, "tp_min": tp_min, "ia_max": ia_max, "ia_min": ia_min,
        "rec_fr": rec_fr, "rec_lat": rec_lat, "rec_fun": rec_fun, "gabarito": gabarito,
        "a_to": a_to, "a_perm_min": a_perm_min, "a_total": a_total, "w_util": w_util, "d_util": d_util,
        "a_recuos": a_recuos, "a_op1_max": a_op1_max, "a_op2_max": a_op2_max, "a_teto_projeto": a_teto_projeto,
        "area_pedida": area_pedida, "a_considerada": a_considerada, "excedeu_area": excedeu_area,
        "to_projeto_pct": to_projeto_pct, "a_livre": a_livre, "a_imperm_poss": a_imperm_poss, "a_ia_saldo": a_ia_saldo,
        "tp_user": tp_user, "status_curto": status_curto, "icon": icon, "explicacao": explicacao,
        "zone_class": zone_class, "via_class": via_class, "via_norm": via_norm,
        "zone_title": zone_title, "desc": desc,
    }


def build_report_payload(calc: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
    rule = calc.get("rule") or {}
    is_corner = bool(session_state.get("lot_is_corner") or calc.get("lot_is_corner"))
    figs = filter_figuras_by_lot_type(extract_figures_from_rule(rule), is_corner=is_corner)
    return {
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "figures": figs,
    }


def render_cover(pdf: ReportPDF, ctx: Dict[str, Any], generated_at: str) -> None:
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    y = pdf.get_y()
    pdf.rounded_rect(pdf.l_margin, y, full_w(pdf), 40, 2.2, style="DF")
    pdf.set_xy(pdf.l_margin + 3, y + 3)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(32, 42, 71)
    pdf.cell(0, 6, san(ctx["uso_label"]))
    pdf.set_xy(pdf.l_margin + 3, y + 10)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 88, 102)
    pdf.multi_cell(full_w(pdf)-42, 5, san(f"Zona {ctx['zone']} | Via: {ctx['via']} | Tipo de lote: {ctx['tipo_lote']} | Emitido em: {generated_at}"))
    pdf.set_xy(pdf.w - pdf.r_margin - 38, y + 6)
    status_badge(pdf, ctx["status_curto"]) 
    pdf.set_xy(pdf.l_margin + 3, y + 19)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0,0,0)
    intro = (
        "Este relatório mostra, de forma simples, o que pode ou não pode ser feito no terreno informado, com base na zona, na via e nas regras urbanísticas do município. "
        "Primeiro mostramos onde o terreno está, depois se o uso é viável, e em seguida explicamos os principais limites do lote, como ocupação, área livre, altura, vagas, ambientes mínimos e calçada."
    )
    pdf.multi_cell(full_w(pdf)-6, 5.0, san(intro))
    pdf.set_y(y + 42)

    section_title(pdf, "", "DADOS PRINCIPAIS DO ESTUDO")
    widths = [42, 42, 42, full_w(pdf) - 126 - 7.5]
    kpi_row(pdf, [
        ("ÁREA DO TERRENO", fmt_area(ctx["area"])),
        ("DIMENSÕES", f"{fmt_num(ctx['front'])} m × {fmt_num(ctx['depth'])} m"),
        ("TIPO DE LOTE", ctx["tipo_lote"]),
        ("SUBZONA / SETOR", ctx["subzona"]),
    ], widths)
    kpi_row(pdf, [
        ("VIA", ctx["via"]),
        ("TIPO DE VIA", ctx["via_tipo"]),
        ("RESULTADO", ctx["status_curto"]),
    ], [70, 45, full_w(pdf)-115-5.0])


def render_item_01(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "01", "Onde está localizado o terreno?")
    paragraph(pdf, "Aqui estão os dados principais usados nesta análise.")
    card_box(pdf, "Dados-base do estudo", [
        f"Uso informado: {ctx['uso_label']}",
        f"Área do terreno: {fmt_area(ctx['area'])}",
        f"Dimensões: {fmt_num(ctx['front'])} m × {fmt_num(ctx['depth'])} m",
        f"Zona: {ctx['zone']}",
        f"Subzona / setor: {ctx['subzona']}",
        f"Tipo de lote: {ctx['tipo_lote']}",
        f"Via: {ctx['via']}",
        f"Tipo de via: {ctx['via_tipo']}",
    ])


def mf_sigla_nome(sigla: str) -> str:
    mapa = {
        "A": "Adequado", "I": "Inadequado", "AP": "Adequado (pequeno porte)",
        "AM": "Adequado (médio porte)", "AP/AM": "Depende do porte", "PE": "Projeto especial"
    }
    return mapa.get(str(sigla).strip().upper(), sigla)


def render_item_02(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "02", "O uso residencial unifamiliar é viável neste terreno?")
    paragraph(pdf, "Para o uso residencial unifamiliar, a permissão pode depender principalmente da zona e, em alguns casos, também do tipo da via.")
    via_line = f"Por via: {ctx['via_tipo'] or 'via local'}"
    if ctx["via_norm"] and ctx["via_class"]:
        via_line = f"Por via: {ctx['via_class']} ({mf_sigla_nome(ctx['via_class'])})"
    body = [
        f"Por zona: {ctx['zone_class'] or 'não encontrado'}" + (f" ({mf_sigla_nome(ctx['zone_class'])})" if ctx['zone_class'] else ""),
        via_line,
        f"Resumo final: {ctx['status_curto']}",
    ]
    tone = (231,245,236) if ctx['status_curto'] == 'PERMITE' else (255,247,237)
    card_box(pdf, "Leitura da viabilidade", body, fill=tone)
    if ctx['explicacao']:
        paragraph(pdf, f"Mesmo quando o resultado for positivo, ainda é necessário cumprir TO, TP, IA, recuos, altura e as demais regras aplicáveis.")


def render_item_03(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "03", "Como funciona a leitura da adequabilidade no unifamiliar?")
    paragraph(pdf, "No unifamiliar, o resultado não depende só do nome da zona. Em alguns casos, também é preciso observar o tipo da via.")
    paragraph(pdf, "Pequeno: até 250 m² | Médio: 250,01 m² até 1.000 m² | Grande: 1.000,01 m² até 5.000 m²")
    paragraph(pdf, "Projeto especial: acima de 5.000 m²")
    simple_table(pdf,
        ["Sigla", "O que significa", "Como interpretar"],
        [
            ["A", "Adequado / permitido", "Pode seguir com o projeto, respeitando as demais regras."],
            ["I", "Inadequado / não permitido", "Em regra, não pode nesse local/condição."],
            ["AP", "Adequado (pequeno porte)", "Pode, mas normalmente limitado a porte pequeno."],
            ["AM", "Adequado (médio porte)", "Pode, mas normalmente limitado a porte médio."],
            ["AP/AM", "Depende do porte", "Pode, mas depende se o caso é pequeno ou médio."],
            ["PE", "Projeto especial", "Pode exigir análise específica e condições extras no licenciamento."],
        ], [18, 58, full_w(pdf)-76], font_size=8.8, line_h=4.7)


def render_item_04(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "04", "O que essa zona permite neste terreno?")
    paragraph(pdf, "Todo terreno está inserido em uma zona, e cada zona pode ter regras, restrições e critérios próprios de uso e ocupação.")
    desc = ctx.get('desc') or {}
    title = ctx.get('zone_title') or ctx['zone']
    if desc and desc.get('description_text'):
        card_box(pdf, f"{title}", [str(desc.get('description_text'))], fill=(248,250,252))
    else:
        card_box(pdf, f"Zona {ctx['zone']}", [
            f"Via do terreno: {ctx['via']}",
            f"Tipo de via: {ctx['via_tipo']}",
        ])


def render_item_05(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "05", "Regras principais para este terreno")
    paragraph(pdf, "Depois de entender a zona, o próximo passo é ver as regras básicas do lote.")
    w = (full_w(pdf)-5.0)/2
    kpi_row(pdf, [("TO MÁXIMA", fmt_pct(ctx['to_max'])), ("TP MÍNIMA", fmt_pct(ctx['tp_min']))], [w,w])
    kpi_row(pdf, [("IA MÁXIMO", fmt_plain(ctx['ia_max'])), ("IA MÍNIMO", fmt_plain(ctx['ia_min']))], [w,w])
    kpi_row(pdf, [("RECUOS", f"F: {fmt_num(ctx['rec_fr'])} m | L: {fmt_num(ctx['rec_lat'])} m | Fu: {fmt_num(ctx['rec_fun'])} m"), ("ALTURA MÁXIMA", fmt_m(ctx['gabarito']))], [full_w(pdf)-45, 42])


def render_item_06(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "06", "Quanto posso ocupar no térreo?")
    if ctx['to_max'] is None or ctx['a_to'] is None:
        card_box(pdf, "Sem dado", ["Sem TO máxima cadastrada para esta zona/uso."], fill=(255,247,237))
        return
    paragraph(pdf, "A Taxa de Ocupação mostra o limite percentual permitido para o térreo.")
    paragraph(pdf, f"A zona permite ocupar até {fmt_pct(ctx['to_max'])} do terreno no térreo.")
    card_box(pdf, "Cálculo da TO", [f"{fmt_area(ctx['area'])} × {fmt_pct(ctx['to_max'])} = {fmt_area(ctx['a_to'])}", "Esse é o limite máximo permitido pela Taxa de Ocupação (TO)."], fill=(243,246,250))
    if not ctx['is_irregular']:
        card_box(pdf, "Opção principal — adotando os recuos da zona", [
            f"Frontal: {fmt_m(ctx['rec_fr'])} | Laterais: {fmt_m(ctx['rec_lat'])} cada | Fundo: {fmt_m(ctx['rec_fun'])}",
            f"Largura útil: {fmt_num(ctx['w_util'])} m | Profundidade útil: {fmt_num(ctx['d_util'])} m",
            f"{fmt_num(ctx['w_util'])} m × {fmt_num(ctx['d_util'])} m = {fmt_area(ctx['a_recuos'])}",
            f"Nessa opção, o limite físico pelos recuos é {fmt_area(ctx['a_op1_max'])}." if ctx['a_op1_max'] is not None else "",
        ])
    card_box(pdf, "Opção alternativa — aproveitando a flexibilidade da lei", [
        "Para residência unifamiliar, a legislação admite zerar o recuo frontal e os recuos laterais, desde que o projeto continue respeitando a TO máxima e a TP mínima.",
        f"Térreo máximo nesta opção: {fmt_area(ctx['a_op2_max'])}" if ctx['a_op2_max'] is not None else "",
    ], fill=(240,253,244))


def render_item_07(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "07", "Quanto preciso deixar livre?")
    if ctx['tp_min'] is None or ctx['a_perm_min'] is None:
        card_box(pdf, "Sem dado", ["Sem TP mínima cadastrada para esta zona/uso."], fill=(255,247,237))
        return
    paragraph(pdf, "Além da ocupação no térreo, a zona exige área permeável mínima.")
    paragraph(pdf, f"A zona exige {fmt_pct(ctx['tp_min'])} de área permeável.")
    card_box(pdf, "Cálculo da TP", [f"{fmt_area(ctx['area'])} × {fmt_pct(ctx['tp_min'])} = {fmt_area(ctx['a_perm_min'])} obrigatórios permeáveis"], fill=(243,246,250))
    if ctx['a_op2_max'] is not None and ctx['area'] is not None:
        a_rest = ctx['area'] - ctx['a_op2_max']
        a_imp = a_rest - ctx['a_perm_min']
        card_box(pdf, "Cenário pela opção principal", [
            f"Usando {fmt_area(ctx['a_op2_max'])} no térreo, sobra {fmt_area(a_rest)} no lote.",
            f"Desses, {fmt_area(ctx['a_perm_min'])} devem permitir infiltração no solo e {fmt_area(a_imp)} podem receber piso impermeável.",
        ], fill=(240,253,244))


def render_item_08(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "08", "Tipos de piso: o que conta como permeável?")
    paragraph(pdf, "Nem todo piso externo conta do mesmo jeito na permeabilidade.")
    simple_table(pdf, ["Tipo de piso", "Percentual considerado permeável"], [[a,b] for a,b in PERMEABILIDADE_ROWS], [110, full_w(pdf)-110], font_size=9)
    paragraph(pdf, "Isso ajuda a entender que nem toda área “livre” do lote conta 100% como permeável.")


def render_item_09(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "09", "Posso construir mais andares?")
    paragraph(pdf, "Além da ocupação no térreo, a zona também define o potencial construtivo total do lote por meio do Índice de Aproveitamento (IA).")
    if ctx['a_total'] is not None:
        card_box(pdf, "Potencial construtivo total", [
            f"{fmt_area(ctx['area'])} × {fmt_plain(ctx['ia_max'])} = {fmt_area(ctx['a_total'])}",
            "Esse é o total que pode ser distribuído entre térreo e pavimentos superiores, respeitando também os demais parâmetros urbanísticos.",
        ], fill=(243,246,250))
    if ctx['gabarito'] is not None:
        card_box(pdf, "Altura máxima da zona", [fmt_m(ctx['gabarito']), "Exemplo simples: adotando pé-direito médio de 3,00 m por pavimento, isso pode permitir algo próximo de 5 pavimentos, apenas como referência inicial."], fill=(248,250,252))


def render_item_10(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "10", "Preciso de vagas de estacionamento?")
    card_box(pdf, "Estacionamento", [
        "Neste caso, não existe exigência mínima obrigatória de vagas de estacionamento.",
        "Essa exigência costuma aparecer em residências multifamiliares e em outras atividades previstas na lei.",
    ], fill=(248,250,252))


def render_item_11(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "11", "Quais medidas mínimas os ambientes precisam ter?")
    paragraph(pdf, "Além das regras do lote, a legislação também traz medidas mínimas para alguns ambientes da edificação.")
    headers = list(QUADRO_ROWS[0].keys())
    rows = [[row[h] for h in headers] for row in QUADRO_ROWS]
    simple_table(pdf, headers, rows, [42, 24, 23, 18, 18, 20, 16], font_size=8.1, line_h=4.5)
    card_box(pdf, "Observações aplicáveis", QUADRO_OBS, fill=(243,246,250))


def render_item_12_intro(pdf: ReportPDF) -> None:
    section_title(pdf, "12", "O que preciso saber sobre a calçada?")
    paragraph(pdf, "A análise não termina dentro do lote. Também existem regras para calçada, acesso ao imóvel, rebaixo de meio-fio e relação do lote com a rua.")


def render_figuras(pdf: ReportPDF, figures: List[Dict[str, Any]]) -> None:
    if not figures:
        return
    temp_files: List[str] = []
    try:
        for idx, fig in enumerate(figures, start=1):
            pdf.add_page()
            titulo = pick_text(fig.get('title'), default=f'Figura {idx}')
            caption = pick_text(fig.get('caption'), default='Anexo V - LC 90/2023')
            section_title(pdf, "12", titulo)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(110,110,110)
            pdf.cell(0, 4.5, san(caption), new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0,0,0)
            url = fig.get('url')
            if not url:
                paragraph(pdf, "Figura sem URL pública disponível.")
                continue
            temp = download_temp_image(url)
            if not temp:
                paragraph(pdf, "Não foi possível carregar esta figura no PDF.")
                continue
            temp_files.append(temp)
            max_w = full_w(pdf)
            max_h = pdf.h - pdf.get_y() - pdf.b_margin - 8
            img_w, img_h = fit_image_size(temp, max_w, max_h)
            x = pdf.l_margin + (full_w(pdf) - img_w) / 2
            pdf.image(temp, x=x, y=pdf.get_y(), w=img_w, h=img_h)
            pdf.set_y(pdf.get_y() + img_h + 2)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(110,110,110)
            pdf.cell(0, 4, san("Anexo V - LC 90/2023"), align="C")
            pdf.set_text_color(0,0,0)
    finally:
        for p in temp_files:
            try:
                os.remove(p)
            except Exception:
                pass


def render_item_13(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "13", "Dicas valiosas")
    for item in get_dicas_valiosas(is_corner=bool(ctx['is_corner'])):
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            titulo = str(item[0] or '').strip()
            texto = str(item[1] or '').strip()
            if texto:
                card_box(pdf, titulo or 'Dica', [texto], fill=(255,247,237))
        else:
            texto = str(item or '').strip()
            if texto:
                card_box(pdf, 'Dica', [texto], fill=(255,247,237))


def render_item_14(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "14", "Resumo rápido final")
    paragraph(pdf, f"{ctx['zone_title']}")
    kpi_row(pdf, [("ZONA", ctx['zone']), ("TO MÁXIMA", fmt_pct(ctx['to_max'])), ("TP MÍNIMA", fmt_pct(ctx['tp_min']))], [40, 40, full_w(pdf)-80-5.0])
    kpi_row(pdf, [("IA MÁXIMO", fmt_plain(ctx['ia_max'])), ("ALTURA MÁXIMA", fmt_m(ctx['gabarito'])), ("ÁREA MÁXIMA NO TÉRREO", fmt_area(ctx['a_to']))], [40, 45, full_w(pdf)-85-5.0])
    kpi_row(pdf, [("ÁREA PERMEÁVEL MÍNIMA", fmt_area(ctx['a_perm_min'])), ("ÁREA TOTAL MÁXIMA", fmt_area(ctx['a_total']))], [88, full_w(pdf)-88-2.5])
    if ctx['area_pedida'] is not None and ctx['a_considerada'] is not None:
        resumo = (
            f"Em resumo: o relatório considerou a área de {fmt_area(ctx['a_considerada'])} no térreo. "
            f"Com isso, a TO considerada ficou em {fmt_pct(ctx['to_projeto_pct'])}, a área livre remanescente em {fmt_area(ctx['a_livre'])} e o saldo estimado pelo IA em {fmt_area(ctx['a_ia_saldo'])}."
        )
    else:
        resumo = (
            f"Em resumo: você pode ocupar até a TO máxima da zona no térreo, precisa manter a TP mínima do terreno permeável, "
            f"pode construir até o IA máximo no total e deve respeitar os limites de altura, recuos e demais exigências urbanísticas."
        )
    card_box(pdf, "Síntese final", [resumo], fill=(243,246,250))


def render_item_15(pdf: ReportPDF) -> None:
    section_title(pdf, "15", "O que acontece depois desta etapa?")
    paragraph(pdf, "Após a finalização dos projetos, será necessário dar entrada na documentação junto à Prefeitura para obter o alvará de construção.")
    card_box(pdf, "Alvará de Construção Simplificado", [
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
    ], fill=(248,250,252))
    card_box(pdf, "Alvará de Construção (Obra Nova)", [
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
    ], fill=(248,250,252))


def render_item_16(pdf: ReportPDF) -> None:
    section_title(pdf, "16", "Fechamento final")
    card_box(pdf, "Fechamento final", [
        "Este relatório foi pensado para ajudar a entender o terreno de forma mais simples.",
        "Na etapa de projeto e aprovação, ainda será preciso conferir os detalhes completos no setor de licenciamento de obras da Prefeitura.",
    ], fill=(243,246,250))


def generate_report_pdf_bytes(calc: Dict[str, Any], session_state: Dict[str, Any]) -> bytes:
    payload = build_report_payload(calc, session_state)
    ctx = extract_context(calc, session_state)

    pdf = ReportPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.set_margins(14, 24, 14)
    pdf.add_page()

    render_cover(pdf, ctx, payload['generated_at'])
    render_item_01(pdf, ctx)
    render_item_02(pdf, ctx)
    render_item_03(pdf, ctx)
    render_item_04(pdf, ctx)
    render_item_05(pdf, ctx)
    render_item_06(pdf, ctx)
    render_item_07(pdf, ctx)
    render_item_08(pdf, ctx)
    render_item_09(pdf, ctx)
    render_item_10(pdf, ctx)
    render_item_11(pdf, ctx)
    render_item_12_intro(pdf)
    render_figuras(pdf, payload.get('figures', []))
    render_item_13(pdf, ctx)
    render_item_14(pdf, ctx)
    render_item_15(pdf)
    render_item_16(pdf)

    pdf.ln(2)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(120,120,120)
    pdf.multi_cell(full_w(pdf), 4.2, san('Documento gerado pelo Viabilidade Fácil com base nos parâmetros urbanísticos exibidos no relatório do sistema.'))

    result = pdf.output(dest='S')
    if isinstance(result, bytearray):
        return bytes(result)
    if isinstance(result, bytes):
        return result
    return result.encode('latin-1', errors='replace')
