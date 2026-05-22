from __future__ import annotations

import json
import re
import os
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any, Dict, List, Optional, Sequence
from urllib.request import urlopen

from fpdf import FPDF

from ui.relatorio_blocks.figuras_anexo_v import filter_figuras_by_lot_type
from ui.relatorio_blocks.multifamiliar_items.common import (
    _fetch_adequabilidade as _mf_fetch_adequabilidade,
    _sigla_nome as _mf_sigla_nome,
    _summarize_adequabilidade as _mf_summarize_adequabilidade,
    _via_tipo_norm as _mf_via_tipo_norm,
)
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
    "Tolerada a iluminação e ventilação zenital.",
    "Poderão utilizar ventilação mecânica ou serem ventilados e iluminados indiretamente através de outros banheiros, circulações, depósitos ou áreas de serviços.",
    "Não poderão comunicar-se diretamente com a cozinha e sala de jantar.",
    "As condições de iluminação e ventilação naturais poderão ser substituídas por meios artificiais.",
    "Para corredores com mais de 5,00m de comprimento, a largura mínima é de 1,00m.",
    "Para corredores com mais de 10,00m de comprimento é obrigatória a ventilação na relação de 1/20 da área do piso.",
    "Poderá ser computada como área de ventilação a área da porta com venezianas.",
    "Deverá ser material incombustível ou tratada para tal.",
    "Serão permitidas escadas em curva, desde que a curvatura interna tenha um raio mínimo de 2,00m e os degraus tenham largura mínima de 0,28m, medida na linha do piso, desenvolvida à distância de 1,00m da linha de curvatura externa.",
    "As exigências da observação 9 ficam dispensadas para escadas tipo marinheiro e caracol, admitidas para acesso a torres, jiraus, adegas, ateliês, escritórios e outros casos especiais.",
    "Serão obrigatórios os patamares intermediários sempre que houver mudança de direção ou quando o lance da escada precisar vencer altura superior a 2,90m; o comprimento do patamar não será inferior à largura da escada.",
    "A largura mínima do degrau será de 0,25m.",
    "A altura máxima do degrau será de 0,19m.",
    "O piso deve ser antiderrapante.",
    "A inclinação máxima será de 10%.",
    "Consideram-se corredores principais os que dão acesso às unidades habitacionais em residências multifamiliares.",
    "Quando a área for superior a 10,00m², deverão ser ventilados na relação de 1/24 da área do piso.",
    "Quando o comprimento for superior a 10,00m, deverá ser alargado de 0,10m por metro, ou fração, do comprimento excedente a 10,00m.",
    "Quando não houver ligação direta com o exterior, será tolerada ventilação por meio de chaminés de ventilação ou pela caixa de escada, nos casos que precisar.",
    "Deverá haver ligação direta entre o hall e a caixa de escada.",
    "Tolerada ventilação pela caixa de escada.",
    "A área mínima de 6,00m² é exigida quando houver um só elevador. Quando houver mais de um elevador, a área deverá ser aumentada de 30% para o elevador excedente.",
    "A área mínima de 12,00m², exigida quando houver um só elevador, deverá ser aumentada de 30% por elevador excedente.",
    "Será tolerado um diâmetro de 2,50m, quando os elevadores se situarem no mesmo lado do hall.",
    "Consideram-se corredores principais os de uso comum do edifício.",
    "Quando a área for superior a 20,00m², deverão ser ventilados na relação de 1/20 da área do piso.",
    "A abertura de ventilação deverá se situar, no máximo, a 10,00m de qualquer ponto do corredor.",
    "Consideram-se corredores secundários os de uso exclusivo da administração do edifício ou destinado a serviço.",
]

QUADRO_GERAIS_OBS = [
    "a) Para o uso residencial o revestimento impermeável das paredes será, no mínimo, até 1,50m na cozinha, banheiro e lavanderia.",
    "b) Para os edifícios de habitação multifamiliar ou coletiva e comerciais, o revestimento impermeável das paredes será, no mínimo até 1,50m nas escadas e sanitários.",
    "c) Para os edifícios de habitação multifamiliar ou coletiva e comerciais, o revestimento impermeável do piso será no hall do prédio, hall dos pavimentos, corredores principais e secundários, escadas, rampas e sanitários.",
    "d) As edificações construídas com estruturas de contêineres devem observar a legislação vigente e apresentar um pé-direito mínimo de 2,40m.",
    "e) Para todos os usos, as colunas iluminação mínima e ventilação mínima deste Anexo referem-se à relação entre a área da abertura e a área do piso.",
]


PERMEABILIDADE_ROWS = [
    ("Grama", "100%"),
    ("Brita solta / terra batida", "100%"),
    ("Piso drenante", "90%"),
    ("Bloco de concreto vazado (piso verde)", "60%"),
    ("Pedra portuguesa / intertravado", "25%"),
]


class ReportPDF(FPDF):
    def __init__(self, *args: Any, trace_footer_text: str = "", **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.trace_footer_text = trace_footer_text

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
        self.set_y(-11)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(140, 148, 160)
        if self.trace_footer_text:
            page_text = san(f"{self.trace_footer_text} | Página {self.page_no()}")
        else:
            page_text = san(f"Página {self.page_no()}")
        self.cell(0, 4, page_text, align="C")


_TRACE_TZ = ZoneInfo("America/Fortaleza")


def _report_trace_footer(session_state: Dict[str, Any]) -> str:
    user_name = str(session_state.get("auth_user_name") or session_state.get("auth_name") or "Usuário não identificado").strip()
    user_email = str(session_state.get("auth_user_email") or session_state.get("auth_email") or "e-mail não informado").strip()
    generated_at = datetime.now(_TRACE_TZ).strftime("%d/%m/%Y %H:%M")
    return f"Uso exclusivo da conta: {user_name} - {user_email} - Gerado em {generated_at} - Viabilidade Fácil"


def san(text: Any) -> str:
    s = str(text)
    replacements = {
        "—": " - ",
        "–": " - ",
        "−": "-",
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "→": " -> ",
        "⇒": " -> ",
        "✅": "",
        "⚠️": "",
        "⚠": "",
        "⛔": "",
        "📍": "",
        "📘": "",
        "🧭": "",
        "📏": "",
        "📐": "",
        "🌿": "",
        "🧱": "",
        "🏢": "",
        "🚗": "",
        "📋": "",
        "🚶": "",
        "📎": "",
        "💡": "",
        "📌": "",
        "🏛️": "",
        "🏗️": "",
        "📄": "",
        "🔎": "",
        "•": "-",
        "1️⃣": "1",
        "2️⃣": "2",
        "3️⃣": "3",
        "4️⃣": "4",
        "5️⃣": "5",
        "6️⃣": "6",
        "7️⃣": "7",
        "8️⃣": "8",
        "9️⃣": "9",
        "0️⃣": "0",
        "\u00a0": " ",
    }
    for a, b in replacements.items():
        s = s.replace(a, b)
    if "\n" in s:
        s = "\n".join(" ".join(line.split()) for line in s.splitlines())
    else:
        s = " ".join(s.split())
    return s.encode("latin-1", "replace").decode("latin-1")

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
    return f"{n:.{dec}f}%".replace(".", ",")


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



def _safe_line_count(pdf: ReportPDF, text: str, width: float, line_h: float = 5.0) -> int:
    """
    Mede o número de linhas de forma robusta.
    Tenta usar dry_run do fpdf2; se a versão não suportar, cai no cálculo matemático
    com get_string_width, que existe em versões antigas também.
    """
    txt = san(text)
    if not txt:
        return 1
    width = max(4.0, float(width))
    try:
        lines = pdf.multi_cell(width, line_h, txt, dry_run=True, output="LINES")
        return max(1, len(lines))
    except Exception:
        total_lines = 0
        for paragraph in txt.split("\n"):
            p = paragraph.strip()
            if not p:
                total_lines += 1
                continue
            words = p.split(" ")
            current_w = 0.0
            lines_in_par = 1
            for word in words:
                token = (word + " ").strip() if word else " "
                token_w = pdf.get_string_width((word + " ") if word else " ")
                if current_w + token_w > width and current_w > 0:
                    lines_in_par += 1
                    current_w = token_w
                else:
                    current_w += token_w
            total_lines += lines_in_par
        return max(1, total_lines)


def ensure_space(pdf: ReportPDF, needed_height: float) -> None:
    """Garante que há espaço suficiente antes de desenhar um bloco."""
    space_left = pdf.h - pdf.b_margin - pdf.get_y()
    if needed_height > space_left:
        pdf.add_page()


def section_title(pdf: ReportPDF, n: str, title: str) -> None:
    ensure_space(pdf, 12)
    pdf.ln(2)
    x = pdf.l_margin
    y = pdf.get_y()
    if not str(n or '').strip():
        pdf.set_font("Helvetica", "B", 12.5)
        pdf.set_text_color(35, 46, 68)
        pdf.multi_cell(full_w(pdf), 6, san(title))
        pdf.set_text_color(0, 0, 0)
        pdf.set_y(y + 8)
        return
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
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B" if bold else "", 10)
    if color:
        pdf.set_text_color(*color)
    pdf.multi_cell(full_w(pdf), h, san(text))
    pdf.set_x(pdf.l_margin)
    pdf.set_text_color(0, 0, 0)


def bullet_list(pdf: ReportPDF, items: Sequence[str]) -> None:
    for it in items:
        ensure_space(pdf, 5.8)
        pdf.set_x(pdf.l_margin + 2)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(full_w(pdf) - 2, 5.2, san(f"- {it}"))
        pdf.set_x(pdf.l_margin)


def card_box(pdf: ReportPDF, title: str, body_lines: Sequence[str], *, fill=(248,250,252), title_color=(29,44,78)) -> None:
    """
    Caixa com look-ahead.
    Se não couber inteira na página, pula antes.
    Se for maior que a área útil da página, entra em modo quebrável.
    """
    line_h = 4.9
    title_h = 4.8
    inner_w = full_w(pdf) - 6
    title_txt = san(title or "")
    body_lines = [str(x) for x in (body_lines or []) if str(x).strip()]

    pdf.set_font("Helvetica", "B", 10.5)
    title_count = _safe_line_count(pdf, title_txt, inner_w, title_h)

    pdf.set_font("Helvetica", "", 10)
    body_h = 0.0
    for line in body_lines:
        body_h += _safe_line_count(pdf, line, inner_w, line_h) * line_h

    total_box_height = 3 + (title_count * title_h) + 2 + body_h + 3
    usable_h = pdf.h - pdf.t_margin - pdf.b_margin - 10

    # Bloco grande demais para uma página: cabeçalho em caixa e corpo paginável
    if total_box_height > usable_h:
        ensure_space(pdf, 11)
        x = pdf.l_margin
        y = pdf.get_y()
        pdf.set_fill_color(*fill)
        pdf.set_draw_color(224, 228, 234)
        pdf.rounded_rect(x, y, full_w(pdf), 9.5, 1.8, style="DF")

        pdf.set_xy(x + 3, y + 2.2)
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(*title_color)
        pdf.multi_cell(inner_w, title_h, title_txt)
        pdf.set_text_color(0, 0, 0)
        pdf.set_y(y + 11)

        pdf.set_font("Helvetica", "", 10)
        for line in body_lines:
            # quebra segura do corpo, sem fundo contínuo
            lines_needed = _safe_line_count(pdf, line, full_w(pdf) - 2, line_h)
            ensure_space(pdf, lines_needed * line_h + 1.5)
            pdf.set_x(pdf.l_margin + 1)
            pdf.multi_cell(full_w(pdf) - 2, line_h, san(line))
            pdf.set_x(pdf.l_margin)
        pdf.ln(1.5)
        return

    ensure_space(pdf, total_box_height + 2)

    x = pdf.l_margin
    y = pdf.get_y()
    pdf.set_fill_color(*fill)
    pdf.set_draw_color(224, 228, 234)
    pdf.rounded_rect(x, y, full_w(pdf), total_box_height, 1.8, style="DF")

    pdf.set_xy(x + 3, y + 2.2)
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(*title_color)
    pdf.multi_cell(inner_w, title_h, title_txt)

    pdf.set_xy(x + 3, y + 3 + (title_count * title_h) + 1.5)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    for line in body_lines:
        pdf.multi_cell(inner_w, line_h, san(line))
        pdf.set_x(x + 3)

    pdf.set_y(y + total_box_height + 2)


def kpi_row(pdf: ReportPDF, items: Sequence[tuple[str, str]], widths: Sequence[float]) -> None:
    """Linha de KPIs com altura simétrica e medição robusta."""
    assert len(items) == len(widths)
    label_h = 3.3
    value_h = 4.4
    row_heights = []

    for (label, value), w in zip(items, widths):
        pdf.set_font("Helvetica", "B", 8.2)
        label_lines = _safe_line_count(pdf, label, w - 4, label_h)
        pdf.set_font("Helvetica", "B", 11)
        value_lines = _safe_line_count(pdf, value, w - 4, value_h)
        row_heights.append(4 + (label_lines * label_h) + 1 + (value_lines * value_h) + 3)

    box_h = max(row_heights + [16.0])
    ensure_space(pdf, box_h + 2)

    x = pdf.l_margin
    y = pdf.get_y()
    for (label, value), w in zip(items, widths):
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(224, 228, 234)
        pdf.rounded_rect(x, y, w, box_h, 1.5, style="DF")

        pdf.set_xy(x + 2, y + 2.2)
        pdf.set_font("Helvetica", "B", 8.2)
        pdf.set_text_color(95, 95, 95)
        pdf.multi_cell(w - 4, label_h, san(label))

        yy = pdf.get_y()
        pdf.set_xy(x + 2, yy + 0.4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(24, 41, 74)
        pdf.multi_cell(w - 4, value_h, san(value), align="L")

        x += w + 2.5

    pdf.set_text_color(0, 0, 0)
    pdf.set_y(y + box_h + 2)


def simple_table(pdf: ReportPDF, headers: List[str], rows: List[List[str]], widths: List[float], *, font_size: int = 9, line_h: float = 5.0) -> None:
    def row_h(row: List[str], bold: bool = False) -> float:
        pdf.set_font("Helvetica", "B" if bold else "", font_size)
        max_lines = 1
        for idx, txt in enumerate(row):
            max_lines = max(max_lines, _safe_line_count(pdf, txt, widths[idx] - 2, line_h))
        return max_lines * line_h + 2

    hh = row_h(headers, True)
    ensure_space(pdf, hh + 2)

    x = pdf.l_margin
    y = pdf.get_y()
    pdf.set_fill_color(235, 241, 250)
    pdf.set_draw_color(220, 224, 230)
    pdf.set_font("Helvetica", "B", font_size)

    for head, w in zip(headers, widths):
        pdf.rect(x, y, w, hh, style="DF")
        pdf.set_xy(x + 1, y + 1)
        pdf.multi_cell(w - 2, line_h, san(head))
        x += w

    pdf.set_y(y + hh)
    flip = False
    for row in rows:
        rh = row_h(row)
        ensure_space(pdf, rh + 1)
        x = pdf.l_margin
        y = pdf.get_y()
        pdf.set_fill_color(*((255,255,255) if not flip else (250,252,255)))
        flip = not flip
        pdf.set_font("Helvetica", "", font_size)
        for txt, w in zip(row, widths):
            pdf.rect(x, y, w, rh, style="DF")
            pdf.set_xy(x + 1, y + 1)
            pdf.multi_cell(w - 2, line_h, san(txt))
            x += w
        pdf.set_y(y + rh)

def status_badge_width(pdf: ReportPDF, text: str) -> float:
    label = (text or 'SEM DADO').strip().upper()
    return max(36, min(58, pdf.get_string_width(san(label)) + 12))

def status_badge(pdf: ReportPDF, text: str, x: float | None = None, y: float | None = None) -> float:
    x = pdf.get_x() if x is None else x
    y = pdf.get_y() if y is None else y
    label = (text or 'SEM DADO').strip().upper()

    if label in {'PERMITE', 'ATENDE'}:
        fill = (231, 245, 236); border = (187, 247, 208); font = (27, 112, 61)
    elif label in {'NÃO PERMITE', 'NAO PERMITE', 'INADEQUADO'}:
        fill = (254, 242, 242); border = (254, 202, 202); font = (153, 27, 27)
    elif label in {'PROJETO ESPECIAL', 'DEPENDE DO PORTE', 'POSSÍVEL PELA VIA', 'POSSIVEL PELA VIA'}:
        fill = (255, 247, 237); border = (253, 215, 170); font = (154, 52, 18)
    elif label == 'SEM DADO':
        fill = (248, 250, 252); border = (203, 213, 225); font = (71, 85, 105)
    else:
        fill = (243, 246, 250); border = (203, 213, 225); font = (51, 65, 85)

    w = status_badge_width(pdf, label)
    pdf.set_fill_color(*fill)
    pdf.set_draw_color(*border)
    pdf.rounded_rect(x, y, w, 9, 1.4, style='DF')
    pdf.set_xy(x, y + 2)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(*font)
    pdf.cell(w, 4, san(label), align='C')
    pdf.set_text_color(0, 0, 0)
    return w

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
    # Preferir o contexto salvo no cálculo evita que um estado antigo da sessão
    # escolha figuras/textos de outro lote ao reabrir ou regerar relatório.
    is_corner = safe_bool(calc.get("lot_is_corner", session_state.get("lot_is_corner", False)))
    is_irregular = safe_bool(calc.get("lot_is_irregular", calc.get("lot_irregular", session_state.get("lot_is_irregular", session_state.get("lot_irregular", False)))))

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
    if is_irregular:
        front = 0.0
        depth = 0.0
        # Terreno irregular continua sem dimensões retangulares para cálculo,
        # mas pode ser meio de quadra ou esquina para textos/figuras de calçada.
        w_util = None
        d_util = None
        a_recuos = None
    else:
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
    tipo_lote = "Terreno irregular" if is_irregular else ("Esquina" if is_corner else "Meio de quadra")
    zone = pick_text(calc.get("zone"), calc.get("zone_sigla"), calc.get("zone_lookup"), rule.get("zone_sigla"))
    via = pick_text(calc.get("via_nome"), calc.get("street_name"), default="-")
    via_tipo = pick_text(calc.get("via_tipo"), calc.get("street_type"), default="-")
    uso = pick_text(calc.get("use_type_code"), default="RES_UNI")
    uso_label = "Residência unifamiliar" if uso.startswith("RES_UNI") else uso
    subzona = pick_text(rule.get("subzona"), rule.get("subzone_code"), calc.get("subzone_code"), default="PADRAO")
    zone_sigla_lookup = pick_text(calc.get("zone_sigla"), calc.get("zone_lookup"), zone, rule.get("zone_sigla"), default="")
    zone_class = pick_text(calc.get("zone_class"), default="")
    via_class = pick_text(calc.get("via_class"), default="")
    if not zone_class and not via_class:
        try:
            zone_class, via_class, _ = _fetch_adequabilidade_unifamiliar(str(zone_sigla_lookup or ""), via_tipo)
        except Exception:
            zone_class, via_class = zone_class, via_class
    if not zone_class and uso.startswith("RES_UNI"):
        zone_class = _fallback_zone_class_unifamiliar(zone_sigla_lookup or zone)
    status_curto = pick_text(calc.get("status_curto"), calc.get("resultado_final"), default="SEM DADO")
    icon = pick_text(calc.get("icon"), default="")
    explicacao = pick_text(calc.get("explicacao"), default="")
    icon, status_curto, explicacao, via_norm = _resolve_status(zone_class, via_tipo, via_class, status_curto, icon, explicacao)
    zone_title = zone
    desc = fetch_zone_desc(zone_sigla_lookup or zone, pick_text(calc.get("subzone_code"), subzona), pick_text(calc.get("zone_label_raw"), zone))
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
    # A irregularidade define a forma do lote; a posição na quadra continua
    # existindo para escolher as figuras corretas de calçada/esquina.
    # Preferir calc evita vazamento de estado antigo da sessão entre relatórios.
    is_corner_for_figures = safe_bool(calc.get("lot_is_corner", session_state.get("lot_is_corner", False)))
    figs = filter_figuras_by_lot_type(extract_figures_from_rule(rule), is_corner=is_corner_for_figures)
    return {
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "figures": figs,
    }



def render_cover(pdf: ReportPDF, ctx: Dict[str, Any], generated_at: str) -> None:
    meta = f"Zona {ctx['zone']} | Via: {ctx['via']} | Tipo de lote: {ctx['tipo_lote']} | Emitido em: {generated_at}"
    intro = (
        "Este relatório mostra, de forma simples, o que pode ou não pode ser feito no terreno informado, com base na zona, na via e nas regras urbanísticas do município. "
        "Primeiro apresentamos a localização do terreno, depois verificamos se o uso é viável e, em seguida, explicamos os principais limites do lote, como ocupação, área permeável, altura, vagas, ambientes mínimos e calçada."
    )

    badge_w = status_badge_width(pdf, ctx['status_curto'])
    gap = 6.0
    title_w = max(74, full_w(pdf) - badge_w - gap - 6)

    try:
        pdf.set_font('Helvetica', 'B', 14.5)
        title_lines = pdf.multi_cell(title_w, 6.1, san(ctx['uso_label']), dry_run=True, output='LINES')
        pdf.set_font('Helvetica', '', 9.4)
        meta_lines = pdf.multi_cell(full_w(pdf) - 6, 4.7, san(meta), dry_run=True, output='LINES')
        intro_lines = pdf.multi_cell(full_w(pdf) - 6, 4.9, san(intro), dry_run=True, output='LINES')
    except Exception:
        title_lines = [ctx['uso_label']]
        meta_lines = [meta]
        intro_lines = [intro]

    title_block_h = max(8, len(title_lines) * 6.1)
    cover_h = max(60, 11 + title_block_h + len(meta_lines) * 4.7 + len(intro_lines) * 4.9 + 12)

    x = pdf.l_margin
    y = pdf.get_y()
    pdf.set_fill_color(247, 249, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rounded_rect(x, y, full_w(pdf), cover_h, 2.4, style='DF')

    pdf.set_xy(x + 3, y + 3)
    pdf.set_font('Helvetica', 'B', 14.5)
    pdf.set_text_color(32, 42, 71)
    pdf.multi_cell(title_w, 6.1, san(ctx['uso_label']))

    badge_x = x + full_w(pdf) - badge_w - 3
    badge_y = y + 3 + max(0, (title_block_h - 9) / 2)
    status_badge(pdf, ctx['status_curto'], x=badge_x, y=badge_y)

    meta_y = y + 4 + title_block_h
    pdf.set_xy(x + 3, meta_y)
    pdf.set_font('Helvetica', '', 9.4)
    pdf.set_text_color(86, 94, 108)
    pdf.multi_cell(full_w(pdf) - 6, 4.7, san(meta))

    pdf.set_xy(x + 3, meta_y + len(meta_lines) * 4.7 + 1.4)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(32, 42, 71)
    pdf.cell(0, 4.6, san('Leitura inicial do relatório'), new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9.9)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(full_w(pdf) - 6, 4.9, san(intro))
    pdf.set_y(y + cover_h + 2.5)

    section_title(pdf, '', 'DADOS PRINCIPAIS DO ESTUDO')
    w3 = (full_w(pdf) - 5.0) / 3
    kpi_row(pdf, [
        ('ÁREA DO TERRENO', fmt_area(ctx['area'])),
        ('DIMENSÕES', f"{fmt_num(ctx['front'])} m × {fmt_num(ctx['depth'])} m"),
        ('TIPO DE LOTE', ctx['tipo_lote']),
    ], [w3, w3, w3])

    # A via principal ganha a linha própria para dar mais presença visual.
    card_box(pdf, 'VIA', [ctx['via']], fill=(248, 250, 252))
    kpi_row(pdf, [
        ('SUBZONA / SETOR', ctx['subzona']),
        ('TIPO DE VIA', ctx['via_tipo']),
        ('RESULTADO', ctx['status_curto']),
    ], [w3, w3, w3])


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


def _fallback_zone_class_unifamiliar(zone_sigla: str | None) -> str | None:
    z = str(zone_sigla or "").strip().upper()
    z = z.replace("—", "-").replace("_", "").replace("/", "").replace(" ", "")
    if not z:
        return None

    allow_a = {
        "ZEIP", "ZCR", "ZOP", "ZAP", "ZAM", "ZPP", "ZOD", "ZEIT", "ZEIC"
    }
    allow_ap = {"ZEIS1", "ZEIS2", "ZEIS3"}
    deny_i = {"ZEPE", "ZEIA", "ZRO"}

    for prefix in allow_a:
        if z.startswith(prefix):
            return "A"
    for prefix in allow_ap:
        if z.startswith(prefix):
            return "AP"
    for prefix in deny_i:
        if z.startswith(prefix):
            return "I"
    return None


def _parse_zone_description_parts(text: str) -> Dict[str, str]:
    raw = str(text or "").strip()
    out: Dict[str, str] = {"intro": "", "o_que_e": "", "o_que_busca": "", "na_pratica": "", "fechamento": ""}
    if not raw:
        return out

    clean = " ".join(raw.replace("\n", " ").split())

    label_map = [
        ("o_que_e", [r"O que é \([^)]*\):", r"O que é:"]),
        ("o_que_busca", [r"O que a zona busca:", r"O que busca:"]),
        ("na_pratica", [r"O que isso significa na prática:", r"Na prática:"]),
    ]

    # tenta separar pelos rótulos conhecidos, mas tolera variações
    positions = []
    for key, pats in label_map:
        found = None
        found_text = None
        for pat in pats:
            m = re.search(pat, clean, flags=re.I)
            if m:
                found = m.start()
                found_text = m.group(0)
                break
        if found is not None:
            positions.append((found, key, found_text))
    positions.sort(key=lambda x: x[0])

    if not positions:
        # fallback editorial: divide em até 3 sentenças iniciais
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean) if s.strip()]
        if sents:
            out["o_que_e"] = sents[0]
        if len(sents) > 1:
            out["o_que_busca"] = sents[1]
        if len(sents) > 2:
            out["na_pratica"] = " ".join(sents[2:4])
        if len(sents) > 4:
            out["fechamento"] = " ".join(sents[4:])
        return out

    first_pos = positions[0][0]
    out["intro"] = clean[:first_pos].strip()

    for idx, (pos, key, matched_text) in enumerate(positions):
        start = pos + len(matched_text)
        end = positions[idx + 1][0] if idx + 1 < len(positions) else len(clean)
        chunk = clean[start:end].strip(" :.-")
        out[key] = chunk

    # tenta puxar fechamento editorial, quando existir
    m_end = re.search(r"(É essa leitura da zona que ajuda.*)$", clean, flags=re.I)
    if m_end:
        out["fechamento"] = m_end.group(1).strip()

    return out

def _fallback_zone_description(zone_sigla: str) -> Dict[str, str]:
    z = str(zone_sigla or "").strip().upper().replace(" ", "")
    if z == "ZAM":
        return {
            "title": "ZAM - Zona de Adensamento Médio",
            "o_que_e": "zona em consolidação, com infraestrutura em implantação ou incompleta, onde o crescimento deve ser moderado.",
            "o_que_busca": "controlar adensamento e orientar crescimento gradual para manter qualidade urbana.",
            "na_pratica": "dá para crescer, mas normalmente com mais controle e atenção à capacidade de infraestrutura local.",
            "fechamento": "É essa leitura da zona que ajuda a entender o que pode ser implantado no lote e com qual porte.",
        }
    if z == "ZAP":
        return {
            "title": "ZAP - Zona de Adensamento Preferencial",
            "o_que_e": "zona estratégica para crescimento mais intenso e organizado, com potencial de formar novas centralidades.",
            "o_que_busca": "estimular adensamento e mistura de usos, fortalecer cidade policêntrica e direcionar ocupação eficiente.",
            "na_pratica": "costuma favorecer projetos urbanos mais intensos, desde que compatíveis com a infraestrutura.",
            "fechamento": "É essa leitura da zona que ajuda a entender o que pode ser implantado no lote e com qual porte.",
        }
    return {}

def _wrapped_line_count(pdf: "ReportPDF", text: str, width: float, line_h: float) -> int:
    txt = san(text)
    if not txt:
        return 1
    try:
        lines = pdf.multi_cell(max(4, width), line_h, txt, dry_run=True, output="LINES")
        return max(1, len(lines))
    except Exception:
        return max(1, txt.count("\n") + 1)


def _fetch_adequabilidade_unifamiliar(zone_sigla: str, via_tipo_texto: str | None) -> tuple[str | None, str | None, dict[str, Any]]:
    attempts: list[tuple[str, str | None, str | None, dict[str, Any]]] = []
    for use_code in ("RES_UNI", "RES_MULTI_R21", "RES_MULTI_R22", "RES_MULTI_R3"):
        zc, vc, dbg = _mf_fetch_adequabilidade(
            zone_sigla=str(zone_sigla or ""),
            via_tipo_texto=via_tipo_texto,
            use_type_code=use_code,
        )
        attempts.append((use_code, zc, vc, dbg))
        if zc or vc:
            dbg = dict(dbg or {})
            dbg["resolved_use_type_code"] = use_code
            return zc, vc, dbg
    final_dbg = dict(attempts[0][3] if attempts else {})
    final_dbg["attempts"] = [{"use_type_code": u, "zone_class": z, "via_class": v} for u, z, v, _ in attempts]
    return None, None, final_dbg



def _resolve_status(zone_class: str | None, via_tipo: str | None, via_class: str | None, current_status: str | None, current_icon: str | None, current_explicacao: str | None) -> tuple[str, str, str, str]:
    z = (zone_class or '').strip().upper()
    vn = _mf_via_tipo_norm(via_tipo)
    vc = (via_class or '').strip().upper()
    raw_status = (current_status or '').strip().upper()
    icon = (current_icon or '').strip()
    explicacao = (current_explicacao or '').strip()

    sem_dado_like = {'', 'SEM DADO', 'NÃO ENCONTRADO', 'NAO ENCONTRADO', 'NÃO LOCALIZADO', 'NAO LOCALIZADO', 'NÃO INFORMADO', 'NAO INFORMADO'}
    status = raw_status if raw_status not in sem_dado_like else ''

    # Heurística simples e estável para unifamiliar:
    # A -> permite ; I -> não permite ; AP/AM/APAM/PE -> depende/PE ; via A sem zona -> possível pela via.
    if not status:
        if z in {'A'}:
            status = 'PERMITE'
        elif z in {'I'} or vc == 'I':
            status = 'NÃO PERMITE'
        elif z in {'AP', 'AM', 'AP/AM', 'APAM'}:
            status = 'DEPENDE DO PORTE'
        elif z == 'PE':
            status = 'PROJETO ESPECIAL'
        elif not z and vc == 'A':
            status = 'POSSÍVEL PELA VIA'
        else:
            _, s2, e2 = _mf_summarize_adequabilidade(zone_class=z or None, via_norm=vn, via_class=vc or None)
            if s2 and s2.strip().upper() not in sem_dado_like:
                status = s2.strip().upper()
                if not explicacao and e2:
                    explicacao = e2

    if not status:
        status = 'SEM DADO'

    if status in {'PERMITE', 'PERMITE PELA ZONA E PELA VIA'}:
        icon = icon or 'OK'
        if status == 'PERMITE PELA ZONA E PELA VIA':
            if not explicacao or 'não foi possível determinar' in explicacao.lower():
                explicacao = 'Resumo final: PERMITE PELA ZONA E PELA VIA. A zona e a via permitem o uso. Ainda é obrigatório cumprir Taxa de Ocupação (TO), Taxa de Permeabilidade (TP), Índice de Aproveitamento (IA), recuos, altura e as demais regras aplicáveis.'
        elif not explicacao or 'não foi possível determinar' in explicacao.lower():
            explicacao = 'Resumo final: PERMITE. A zona permite. Ainda é obrigatório cumprir Taxa de Ocupação (TO), Taxa de Permeabilidade (TP), Índice de Aproveitamento (IA), recuos, altura e as demais regras aplicáveis.'
    elif status == 'NÃO PERMITE':
        icon = icon or 'X'
        explicacao = explicacao or 'Resumo final: NÃO PERMITE. Em regra, a leitura atual não favorece a implantação desse uso nesta condição.'
    elif status == 'DEPENDE DO PORTE':
        icon = icon or 'ATENCAO'
        explicacao = explicacao or 'Resumo final: DEPENDE DO PORTE. A possibilidade depende do porte do empreendimento e das demais regras aplicáveis.'
    elif status == 'PROJETO ESPECIAL':
        icon = icon or 'ATENCAO'
        explicacao = explicacao or 'Resumo final: PROJETO ESPECIAL. O caso pode exigir análise específica e condições extras no licenciamento.'
    elif status in {'POSSÍVEL PELA VIA', 'POSSIVEL PELA VIA'}:
        icon = icon or 'ATENCAO'
        explicacao = explicacao or 'Resumo final: POSSÍVEL PELA VIA. A leitura por via é favorável, mas a adequabilidade por zona não foi localizada automaticamente.'
    else:
        status = 'SEM DADO'
        icon = icon or 'ATENCAO'
        explicacao = explicacao or 'Não foi possível determinar automaticamente o resultado por zona.'

    return icon, status, explicacao, vn or ''


def render_item_02(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "02", "O uso residencial unifamiliar é viável neste terreno?")
    paragraph(pdf, "Para o uso residencial unifamiliar, a permissão pode depender principalmente da zona e, em alguns casos, também do tipo da via.")

    zone_class = (ctx.get('zone_class') or '').strip().upper()
    via_class = (ctx.get('via_class') or '').strip().upper()
    via_norm = ctx.get('via_norm') or ''
    status = (ctx.get('status_curto') or 'SEM DADO').strip().upper()

    zona_line = f"Por zona: {zone_class} ({mf_sigla_nome(zone_class)})" if zone_class else "Por zona: não encontrado"
    if via_norm in {'via local', 'local', ''} and not via_class:
        via_line = f"Por via: {ctx['via_tipo'] or 'via local'}"
    elif via_class:
        via_line = f"Por via: {via_class} ({mf_sigla_nome(via_class)})"
    else:
        via_line = f"Por via: {ctx['via_tipo'] or '-'}"

    if status in {'PERMITE', 'PERMITE PELA ZONA E PELA VIA'}:
        fill = (231, 245, 236)
        if status == 'PERMITE PELA ZONA E PELA VIA':
            resumo = "PERMITE PELA ZONA E PELA VIA. A zona e a via permitem o uso. Ainda é obrigatório cumprir Taxa de Ocupação (TO), Taxa de Permeabilidade (TP), Índice de Aproveitamento (IA), recuos, altura e as demais regras aplicáveis."
        else:
            resumo = "PERMITE. A zona permite. Ainda é obrigatório cumprir Taxa de Ocupação (TO), Taxa de Permeabilidade (TP), Índice de Aproveitamento (IA), recuos, altura e as demais regras aplicáveis."
        reforco = "Mesmo quando o resultado for positivo, ainda é necessário cumprir Taxa de Ocupação (TO), Taxa de Permeabilidade (TP), Índice de Aproveitamento (IA), recuos, altura e as demais regras aplicáveis."
    elif status == 'NÃO PERMITE':
        fill = (254, 242, 242)
        resumo = "NÃO PERMITE. Em regra, a leitura atual não favorece a implantação desse uso nesta condição."
        reforco = "Quando o resultado for negativo, a análise da zona, da via e das demais exigências urbanísticas continua sendo essencial para confirmação do caso concreto."
    elif status in {'DEPENDE DO PORTE', 'PROJETO ESPECIAL', 'POSSÍVEL PELA VIA', 'POSSIVEL PELA VIA'}:
        fill = (255, 247, 237)
        resumo = (ctx.get('explicacao') or status).replace('Resumo final:', '').strip()
        reforco = "Mesmo com leitura parcialmente favorável, a definição final ainda depende do porte, da via e das demais exigências urbanísticas aplicáveis."
    else:
        fill = (255, 247, 237)
        resumo = (ctx.get('explicacao') or "Não foi possível determinar automaticamente o resultado por zona.").replace('Resumo final:', '').strip()
        reforco = "Quando a leitura automática não localizar o resultado completo, o caso ainda deve ser confirmado com a leitura da zona, da via e das demais regras urbanísticas aplicáveis."

    card_box(pdf, "Leitura da viabilidade", [zona_line, via_line, f"Resumo final: {status}"], fill=fill)
    card_box(pdf, "Conclusão", [resumo], fill=fill)
    paragraph(pdf, reforco, bold=True)

def render_item_03(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "03", "Como funciona a leitura da adequabilidade no unifamiliar?")
    paragraph(pdf, "No unifamiliar, o resultado não depende só do nome da zona. Em alguns casos, também é preciso observar o tipo da via. Por isso, estas siglas ajudam a interpretar corretamente a viabilidade mostrada acima.")
    paragraph(pdf, "Leitura de siglas", bold=True, color=(32, 42, 71))
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
    paragraph(pdf, "Leitura de porte", bold=True, color=(32, 42, 71))
    simple_table(pdf,
        ["Porte", "Faixa (área construída total)"],
        [
            ["Pequeno", "até 250 m²"],
            ["Médio", "de 250,01 m² até 1.000 m²"],
            ["Grande", "de 1.000,01 m² até 5.000 m²"],
            ["Projeto especial", "acima de 5.000 m²"],
        ], [35, full_w(pdf)-35], font_size=9, line_h=4.9)


def render_item_04(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "04", "O que essa zona permite neste terreno?")
    paragraph(pdf, "A zona identificada para o terreno ajuda a entender quais regras urbanísticas se aplicam ao lote. Ela orienta o uso permitido, a ocupação máxima no térreo, a área permeável mínima, os recuos, a altura e outros cuidados do projeto. Em zonas especiais, ambientais, patrimoniais, econômicas ou de proteção da paisagem, a análise pode exigir confirmação adicional no licenciamento antes de qualquer aprovação.")

    desc = ctx.get('desc') or {}
    title = ctx.get('zone_title') or ctx['zone']
    card_box(pdf, "Zona analisada", [title], fill=(243, 246, 250))

    parts = {}
    if desc and desc.get('description_text'):
        parts = _parse_zone_description_parts(str(desc.get('description_text')))
    if not any(parts.get(k) for k in ("o_que_e","o_que_busca","na_pratica")):
        parts = _fallback_zone_description(ctx['zone']) or parts

    if parts.get("intro"):
        paragraph(pdf, parts["intro"])
    if parts.get("o_que_e"):
        card_box(pdf, f"O que é ({ctx['zone']})", [parts["o_que_e"]], fill=(248, 250, 252))
    if parts.get("o_que_busca"):
        card_box(pdf, "O que a zona busca", [parts["o_que_busca"]], fill=(248, 250, 252))
    if parts.get("na_pratica"):
        card_box(pdf, "O que isso significa na prática", [parts["na_pratica"]], fill=(240, 253, 244))
    fechamento = parts.get("fechamento") or "É essa leitura da zona que ajuda a entender o que pode ser implantado no lote e com qual porte."
    paragraph(pdf, fechamento, bold=True)

def render_item_05(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "05", "Regras principais para este terreno")
    paragraph(pdf, "Depois de entender a zona, o próximo passo é ver as regras básicas do lote.")
    card_box(pdf, "Leitura executiva do lote", [
        "Para este terreno, vale olhar principalmente a ocupação máxima no térreo, a área permeável mínima, os recuos, a altura máxima e o potencial total de construção."
    ], fill=(243, 246, 250))
    paragraph(pdf, "Painel executivo dos parâmetros", bold=True, color=(32, 42, 71))
    w3 = (full_w(pdf) - 5.0) / 3
    kpi_row(pdf, [
        ("Taxa de Ocupação (TO) máxima", fmt_pct(ctx['to_max'])),
        ("Taxa de Permeabilidade (TP) mínima", fmt_pct(ctx['tp_min'])),
        ("Índice de Aproveitamento (IA) máximo", fmt_plain(ctx['ia_max'])),
    ], [w3, w3, w3])
    kpi_row(pdf, [
        ("Índice de Aproveitamento (IA) mínimo", "não informado" if fmt_plain(ctx['ia_min']) == '-' else fmt_plain(ctx['ia_min'])),
        ("ALTURA MÁXIMA", fmt_m(ctx['gabarito'])),
        ("ÁREA MÁXIMA NO TÉRREO", fmt_area(ctx['a_to'])),
    ], [w3, w3, w3])
    card_box(pdf, "RECUOS", [
        f"Frontal: {fmt_num(ctx['rec_fr'])} m",
        f"Laterais: {fmt_num(ctx['rec_lat'])} m",
        f"Fundos: {fmt_num(ctx['rec_fun'])} m",
    ], fill=(248,250,252))
    card_box(pdf, "Leitura final das regras", [
        "Esses são os parâmetros que mais impactam a implantação do projeto no lote e a definição do potencial construtivo inicial."
    ], fill=(237, 245, 255))


def render_item_06(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "06", "Quanto posso ocupar no térreo?")
    if ctx['to_max'] is None or ctx['a_to'] is None:
        card_box(pdf, "Sem dado", ["Sem Taxa de Ocupação (TO) máxima cadastrada para esta zona/uso."], fill=(255,247,237))
        return
    paragraph(pdf, f"A zona permite ocupar até {fmt_pct(ctx['to_max'])} do terreno no térreo.")
    card_box(pdf, "Cálculo da Taxa de Ocupação (TO)", [f"{fmt_area(ctx['area'])} × {fmt_pct(ctx['to_max'])} = {fmt_area(ctx['a_to'])}", "Esse é o limite máximo permitido pela Taxa de Ocupação (TO)."], fill=(243,246,250))
    paragraph(pdf, "Como complemento a essa verificação, também é importante analisar a área que efetivamente cabe no lote, considerando os recuos aplicáveis.")
    card_box(pdf, "Art. 112 — Flexibilidade de recuos", [
        "Será aplicado, para as atividades atrativas de vizinhança de pequeno porte e para o uso residencial unifamiliar, a flexibilidade quanto aos recuos de frente e laterais, podendo zerar, desde que observado o cumprimento da Taxa de Permeabilidade Mínima e da Taxa de Ocupação Máxima da zona em que se encontra.",
        "Na prática: para residência unifamiliar, a norma permite encostar nas laterais e alinhar na frente, desde que o projeto continue respeitando a Taxa de Ocupação (TO) máxima e a Taxa de Permeabilidade (TP) mínima.",
    ], fill=(240,253,244))
    paragraph(pdf, "A partir disso, este lote pode ser lido de duas formas:")
    card_box(pdf, "Cenário A — leitura com flexibilidade do Art. 112", [
        "Para este caso, a legislação admite zerar o recuo frontal e os recuos laterais.",
        "Assim, o térreo pode aproveitar melhor a área do lote, desde que continue respeitando a Taxa de Ocupação (TO) e a Taxa de Permeabilidade (TP).",
        f"Térreo máximo nesta opção: {fmt_area(ctx['a_op2_max'])}" if ctx['a_op2_max'] is not None else "",
        "O recuo de fundo e as demais exigências urbanísticas aplicáveis continuam precisando ser respeitados.",
    ], fill=(240,253,244))
    if not ctx['is_irregular']:
        card_box(pdf, "Cenário B — leitura com recuos padrão da zona", [
            f"Frontal: {fmt_m(ctx['rec_fr'])}",
            f"Laterais: {fmt_m(ctx['rec_lat'])} cada",
            f"Fundo: {fmt_m(ctx['rec_fun'])}",
            "Com isso, a área útil de implantação no térreo passa a ser:",
            f"Largura útil: {fmt_num(ctx['w_util'])} m",
            f"Profundidade útil: {fmt_num(ctx['d_util'])} m",
            f"{fmt_num(ctx['w_util'])} × {fmt_num(ctx['d_util'])} = {fmt_area(ctx['a_recuos'])}",
            f"Nesse cenário, mesmo que a zona permita até {fmt_area(ctx['a_to'])} pela Taxa de Ocupação (TO), o limite físico de implantação, considerando os recuos, fica em {fmt_area(ctx['a_op1_max'])}." if ctx['a_op1_max'] is not None else "",
        ], fill=(248,250,252))
    card_box(pdf, "Leitura prática", [
        f"Pela Taxa de Ocupação (TO), o lote pode ocupar até {fmt_area(ctx['a_to'])} no térreo.",
        f"Na leitura com a flexibilidade do art. 112, o aproveitamento do térreo pode chegar ao limite máximo permitido pela zona, desde que sejam respeitadas a Taxa de Ocupação (TO), a Taxa de Permeabilidade (TP) e as demais exigências aplicáveis.",
        (f"Na leitura com os recuos padrão da zona, a área útil de implantação fica em {fmt_area(ctx['a_op1_max'])}." if ctx['a_op1_max'] is not None else ""),
        ("Neste caso, sem uma área pretendida informada, o estudo passa a apresentar os dois referenciais principais do lote: o limite máximo pela Taxa de Ocupação (TO) e o limite físico de implantação considerando os recuos." if ctx['area_pedida'] is None else ""),
    ], fill=(243,246,250))


def render_item_07(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "07", "Quanto preciso deixar permeável?")
    if ctx['tp_min'] is None or ctx['a_perm_min'] is None:
        card_box(pdf, "Sem dado", ["Sem Taxa de Permeabilidade (TP) mínima cadastrada para esta zona/uso."], fill=(255,247,237))
        return
    paragraph(pdf, f"A zona exige {fmt_pct(ctx['tp_min'])} de área permeável.")
    card_box(pdf, "Cálculo da Taxa de Permeabilidade (TP)", [f"{fmt_area(ctx['area'])} × {fmt_pct(ctx['tp_min'])} = {fmt_area(ctx['a_perm_min'])} obrigatórios permeáveis", "Isso quer dizer que parte do terreno precisa continuar permitindo a infiltração da água da chuva no solo."], fill=(243,246,250))
    paragraph(pdf, "Ver cenários usando os máximos das opções")
    if ctx['a_op2_max'] is not None and ctx['area'] is not None:
        a_rest = ctx['area'] - ctx['a_op2_max']
        a_imp = a_rest - ctx['a_perm_min']
        card_box(pdf, "Cenário A — leitura com flexibilidade do Art. 112", [
            f"Se você utilizar {fmt_area(ctx['a_op2_max'])} no térreo:",
            f"Área sem ocupação no térreo: {fmt_area(ctx['area'])} − {fmt_area(ctx['a_op2_max'])} = {fmt_area(a_rest)}",
            f"{fmt_area(ctx['a_perm_min'])} devem permitir infiltração no solo",
            f"{fmt_area(a_imp)} podem receber piso impermeável",
        ], fill=(240,253,244))
    if ctx['a_op1_max'] is not None and ctx['area'] is not None:
        a_rest1 = ctx['area'] - ctx['a_op1_max']
        a_imp1 = a_rest1 - ctx['a_perm_min']
        card_box(pdf, "Cenário B — leitura com recuos padrão da zona", [
            f"Se você utilizar {fmt_area(ctx['a_op1_max'])} no térreo:",
            f"Área sem ocupação no térreo: {fmt_area(ctx['area'])} − {fmt_area(ctx['a_op1_max'])} = {fmt_area(a_rest1)}",
            f"{fmt_area(ctx['a_perm_min'])} devem permitir infiltração no solo",
            f"{fmt_area(a_imp1)} podem receber piso impermeável",
        ], fill=(248,250,252))
    card_box(pdf, "Leitura prática", [
        "Nas duas opções, o lote precisa manter a área permeável mínima. A diferença está em quanto resta sem ocupação no térreo além desse mínimo.",
    ], fill=(243,246,250))


def render_item_08(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "08", "Tipos de piso: o que conta como permeável?")
    paragraph(pdf, "Nem todo piso externo conta do mesmo jeito na permeabilidade.")
    simple_table(pdf, ["Tipo de piso", "Percentual considerado permeável"], [[a,b] for a,b in PERMEABILIDADE_ROWS], [110, full_w(pdf)-110], font_size=9)
    paragraph(pdf, "Isso ajuda a entender que nem toda área sem ocupação no térreo conta 100% como permeável.")


def render_item_09(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "09", "Posso construir mais andares?")
    paragraph(pdf, "Além da ocupação no térreo, a zona também define o potencial construtivo total do lote por meio do Índice de Aproveitamento (IA).")

    if ctx['a_total'] is not None:
        card_box(pdf, "Potencial construtivo total", [
            f"Se o Índice de Aproveitamento (IA) máximo da zona for {fmt_plain(ctx['ia_max'])}, então o potencial construtivo total do lote será:",
            f"{fmt_area(ctx['area'])} × {fmt_plain(ctx['ia_max'])} = {fmt_area(ctx['a_total'])}",
            "Esse é o total que pode ser distribuído entre térreo e pavimentos superiores, respeitando também os demais parâmetros urbanísticos.",
        ], fill=(243, 246, 250))

    if ctx['gabarito'] is not None:
        g_text = fmt_m(ctx['gabarito'])
        card_box(pdf, "Altura máxima da zona", [
            f"Altura máxima da zona: {g_text}",
            f"A altura máxima de {g_text} é um parâmetro geral da zona. Isso não significa autorização automática para uma residência unifamiliar atingir essa altura ou construir muitos pavimentos.",
            "No caso de uma residência unifamiliar, a altura real da edificação depende do projeto arquitetônico, da implantação no lote, da Taxa de Ocupação (TO), da Taxa de Permeabilidade (TP), dos recuos, do Índice de Aproveitamento (IA), das normas técnicas aplicáveis e da confirmação no licenciamento municipal.",
        ], fill=(248, 250, 252))

def render_item_10(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "10", "Preciso de vagas de estacionamento?")
    card_box(pdf, "Estacionamento", [
        "Neste caso, não existe exigência mínima obrigatória de vagas de estacionamento.",
        "Essa exigência costuma aparecer em residências multifamiliares e em outras atividades previstas na lei.",
    ], fill=(248,250,252))


def render_item_11(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "11", "Quais medidas mínimas os ambientes precisam ter?")
    paragraph(pdf, "Além das regras do lote, a legislação também traz medidas mínimas para alguns ambientes da edificação. Isso vale para itens como sala, quartos, cozinha, banheiro, área de serviço, garagem e escada.")
    paragraph(pdf, "Quadro técnico — parâmetros dos ambientes", bold=True, color=(32, 42, 71))
    paragraph(pdf, "Lei Complementar nº 90/2023 — Anexo II")
    headers = list(QUADRO_ROWS[0].keys())
    rows = [[row[h] for h in headers] for row in QUADRO_ROWS]
    simple_table(pdf, headers, rows, [42, 24, 23, 18, 18, 20, 16], font_size=8.1, line_h=4.5)
    card_box(pdf, "Observações", QUADRO_OBS, fill=(243,246,250))
    card_box(pdf, "Observações gerais", QUADRO_GERAIS_OBS, fill=(248,250,252))


def render_item_12_intro(pdf: ReportPDF) -> None:
    section_title(pdf, "12", "O que preciso saber sobre a calçada?")
    paragraph(pdf, "A análise não termina dentro do lote. Também existem regras para calçada, acesso ao imóvel, rebaixo de meio-fio e relação do lote com a rua. As figuras abaixo ajudam a visualizar esse padrão.")
    paragraph(pdf, "Figuras anexas (Anexo V)", bold=True, color=(32, 42, 71))


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
    pdf.add_page()
    section_title(pdf, "13", "Dicas valiosas")
    card_box(pdf, "Como ler estas orientações", [
        "As dicas abaixo ajudam a interpretar o relatório de forma mais prática, especialmente em temas que costumam gerar dúvida no desenvolvimento do projeto."
    ], fill=(243, 246, 250))
    card_box(pdf, "1. Flexibilidade de recuos", [
        "Art. 112. Será aplicado, para as atividades atrativas de vizinhança de pequeno porte e para o uso residencial unifamiliar, a flexibilidade quanto aos recuos de frente e laterais, podendo zerar, desde que observado o cumprimento da Taxa de Permeabilidade Mínima e da Taxa de Ocupação Máxima da zona em que se encontra.",
        "Na prática: para residência unifamiliar, a legislação admite zerar recuos frontal e laterais, desde que a proposta continue respeitando a Taxa de Permeabilidade (TP) mínima e a Taxa de Ocupação (TO) máxima da zona."
    ], fill=(255, 247, 237))
    card_box(pdf, "2. Calçada", [
        "Não existe uma largura única e fixa para toda calçada no município.",
        "Quando houver padrão definido no loteamento ou na via, ele deve ser seguido. Quando não houver, a referência costuma ser a calçada já existente no local."
    ], fill=(239, 246, 255))
    # contrato legado: card_box(pdf, "3. Piscina e TO"
    # contrato legado: card_box(pdf, "4. Art. 144 e leitura prática"
    card_box(pdf, "3. Piscinas, espelhos d’água, caixas d’água, cisternas e tanques", [
        "Atenção: para a Taxa de Ocupação (TO), a piscina não é contada como área construída do lote.",
        "Art. 144. As piscinas, espelhos d’água, caixas d’água, cisternas e tanques deverão observar afastamento mínimo de 0,50 m de todas as divisas do terreno e devem ser computados como área impermeável para o cálculo da Taxa de Permeabilidade (TP).",
        "Na prática: além de respeitar esse afastamento mínimo de 50 cm, esses elementos também entram no cálculo da Taxa de Permeabilidade (TP) como área impermeável."
    ], fill=(254, 249, 195))


def render_item_14(pdf: ReportPDF, ctx: Dict[str, Any]) -> None:
    section_title(pdf, "14", "Resumo rápido final")
    card_box(pdf, "Síntese executiva do terreno", [
        f"Uso analisado: {ctx['uso_label']}",
        f"Zona: {ctx['zone_title']}",
        f"Tipo de lote: {ctx['tipo_lote']}",
        f"Via: {ctx['via']}",
        f"Tipo de via: {ctx['via_tipo']}",
    ], fill=(243,246,250))
    w2 = (full_w(pdf) - 2.5) / 2
    kpi_row(pdf, [
        ("Taxa de Ocupação (TO) máxima", fmt_pct(ctx['to_max'])),
        ("Taxa de Permeabilidade (TP) mínima", fmt_pct(ctx['tp_min'])),
    ], [w2, w2])
    kpi_row(pdf, [
        ("Índice de Aproveitamento (IA) máximo", fmt_plain(ctx['ia_max'])),
        ("ALTURA MÁXIMA", fmt_m(ctx['gabarito'])),
    ], [w2, w2])
    kpi_row(pdf, [
        ("ÁREA MÁXIMA NO TÉRREO", fmt_area(ctx['a_to'])),
        ("ÁREA PERMEÁVEL MÍNIMA", fmt_area(ctx['a_perm_min'])),
    ], [w2, w2])
    card_box(pdf, "ÁREA Taxa de Ocupação (TO)TAL MÁXIMA ESTIMADA", [fmt_area(ctx['a_total'])], fill=(248,250,252))
    resumo = (
        f"Em resumo: você pode ocupar até {fmt_pct(ctx['to_max'])} do lote no térreo; precisa manter pelo menos {fmt_pct(ctx['tp_min'])} do terreno permeável; a construção pode chegar até {fmt_plain(ctx['ia_max'])} vezes a área do lote no total; e a altura deve respeitar o limite da zona."
    )
    card_box(pdf, "Leitura final", [resumo], fill=(237, 245, 255))


def render_item_15(pdf: ReportPDF) -> None:
    section_title(pdf, "15", "O que acontece depois desta etapa?")
    paragraph(pdf, "Após a finalização dos projetos, será necessário dar entrada na documentação junto à Prefeitura para obter o alvará de construção.")
    paragraph(pdf, "De forma geral, esse processo pode seguir por duas vias:")
    bullet_list(pdf, [
        "Alvará de Construção Simplificado → voltado para casos mais simples e de menor porte;",
        "Alvará de Construção (Obra Nova) → usado quando a obra exige análise técnica mais completa e documentação complementar.",
    ])
    paragraph(pdf, "Abaixo, apresentamos um resumo dos dois caminhos e um checklist básico dos itens que normalmente precisam ser providenciados.")
    card_box(pdf, "Alvará de Construção Simplificado", [
        "O Alvará de Construção Simplificado é uma forma mais rápida de licenciamento, voltada para casos mais simples. Ele costuma ser usado para residência unifamiliar e para comércio/serviços de pequeno porte, com área construída de até 250,00 m².",
        "A lógica desse alvará é mais enxuta e autodeclaratória, mas isso não elimina a necessidade de apresentar os documentos corretos e atender às exigências urbanísticas e técnicas do Município.",
        "Checklist — documentos e itens principais:",
        "[ ] Documento de identidade do requerente ou representante legal",
        "[ ] CPF ou CNPJ",
        "[ ] Matrícula atualizada do imóvel ou documento equivalente",
        "[ ] Certidão negativa de IPTU",
        "[ ] Parecer favorável de Adequabilidade Locacional",
        "[ ] Tabela com índices urbanísticos e áreas da edificação",
        "[ ] Projeto arquitetônico em arquivo digital",
        "[ ] ART/RRT do responsável técnico",
        "[ ] Termo de responsabilidade do responsável técnico",
        "[ ] Termo de responsabilidade do proprietário",
        "[ ] Isenção da licença ambiental",
        "Atenção:",
        "[ ] Confirmar se o caso realmente se enquadra como simplificado",
        "[ ] Conferir se a área construída está dentro do limite permitido",
        "[ ] Protocolar o pedido com antecedência mínima indicada pelo procedimento",
        "[ ] Verificar se todos os arquivos digitais estão prontos e legíveis",
    ], fill=(248,250,252))
    card_box(pdf, "Alvará de Construção (Obra Nova)", [
        "O Alvará de Construção (Obra Nova) é o caminho regular de licenciamento para obras novas que exigem análise técnica completa da Prefeitura. Ele é mais detalhado e costuma ser necessário em casos que não se enquadram no procedimento simplificado ou que exigem documentação complementar.",
        "Esse tipo de alvará pede uma conferência mais ampla do projeto, incluindo aspectos urbanísticos, arquitetônicos, hidrossanitários, ambientais e, em alguns casos, exigências de outros órgãos.",
        "Checklist — documentos principais:",
        "[ ] Requerimento único",
        "[ ] Documento de identidade do requerente ou representante legal",
        "[ ] CPF ou CNPJ",
        "[ ] Matrícula atualizada do imóvel",
        "[ ] Autorização do proprietário, quando necessária",
        "[ ] BCI",
        "[ ] ART/RRT com comprovante de pagamento",
        "[ ] Projeto arquitetônico assinado",
        "[ ] Projeto hidrossanitário",
        "[ ] Memorial de cálculo e drenagem pluvial",
        "[ ] Declaração do SAAE sobre rede de esgoto, quando necessária",
        "Checklist — documentos adicionais que podem ser exigidos:",
        "[ ] Aprovação do Corpo de Bombeiros",
        "[ ] Aprovação do IPHAN, quando o imóvel estiver em ZEIP",
        "[ ] Licenciamento ambiental ou termo de isenção",
        "[ ] PGRSCC",
        "[ ] Autorização do COMAR, quando aplicável",
        "[ ] Aprovação do DNIT ou SOP, quando houver acesso por rodovia",
        "[ ] EIV, quando exigido pela legislação",
        "Atenção:",
        "[ ] Confirmar se o caso realmente exige alvará regular de obra nova",
        "[ ] Conferir se há exigência de documentos complementares por localização ou tipologia",
        "[ ] Verificar se o imóvel está em área com proteção especial",
        "[ ] Conferir se o projeto atende às exigências técnicas antes do protocolo",
    ], fill=(248,250,252))


def render_item_16(pdf: ReportPDF) -> None:
    section_title(pdf, "16", "Fechamento final")
    card_box(pdf, "Fechamento final", [
        "Este relatório é uma análise inicial para ajudar a entender o potencial urbanístico do terreno.",
        "Ele não representa aprovação automática da Prefeitura e não substitui alvará, licença, certidão, parecer técnico ou análise oficial do órgão competente.",
        "Antes de construir, reformar, regularizar, parcelar ou protocolar um projeto, é necessário confirmar as informações do lote, a documentação do imóvel, as regras da zona, as condições da via e as exigências do licenciamento municipal.",
        "A decisão final sobre a aprovação do projeto cabe sempre ao órgão público responsável.",
    ], fill=(243,246,250))


def generate_report_pdf_bytes(calc: Dict[str, Any], session_state: Dict[str, Any]) -> bytes:
    payload = build_report_payload(calc, session_state)
    ctx = extract_context(calc, session_state)

    pdf = ReportPDF(orientation='P', unit='mm', format='A4', trace_footer_text=_report_trace_footer(session_state))
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
