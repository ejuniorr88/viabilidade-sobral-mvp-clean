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


QUADRO_ROWS: List[Dict[str, str]] = [
    {"AMBIENTE": "Sala de estar", "CÍRCULO INSCRITO": "2,00 m", "ÁREA MÍNIMA": "8,00 m²", "ILUMINAÇÃO": "1/8", "VENTILAÇÃO": "1/12", "PÉ-DIREITO": "2,50 m", "OBS.": "7"},
    {"AMBIENTE": "Sala de jantar", "CÍRCULO INSCRITO": "2,00 m", "ÁREA MÍNIMA": "6,00 m²", "ILUMINAÇÃO": "1/8", "VENTILAÇÃO": "1/12", "PÉ-DIREITO": "2,50 m", "OBS.": "7"},
    {"AMBIENTE": "Cozinha", "CÍRCULO INSCRITO": "1,80 m", "ÁREA MÍNIMA": "5,00 m²", "ILUMINAÇÃO": "1/8", "VENTILAÇÃO": "1/12", "PÉ-DIREITO": "2,50 m", "OBS.": "1-7"},
    {"AMBIENTE": "1º e 2º quartos", "CÍRCULO INSCRITO": "2,00 m", "ÁREA MÍNIMA": "8,00 m²", "ILUMINAÇÃO": "1/8", "VENTILAÇÃO": "1/12", "PÉ-DIREITO": "2,50 m", "OBS.": "–"},
    {"AMBIENTE": "Demais quartos", "CÍRCULO INSCRITO": "2,00 m", "ÁREA MÍNIMA": "5,00 m²", "ILUMINAÇÃO": "1/8", "VENTILAÇÃO": "1/12", "PÉ-DIREITO": "2,50 m", "OBS.": "–"},
    {"AMBIENTE": "Banheiro", "CÍRCULO INSCRITO": "1,00 m", "ÁREA MÍNIMA": "1,50 m²", "ILUMINAÇÃO": "1/10", "VENTILAÇÃO": "1/16", "PÉ-DIREITO": "2,20 m", "OBS.": "1-2-3"},
    {"AMBIENTE": "Área de serviço", "CÍRCULO INSCRITO": "1,20 m", "ÁREA MÍNIMA": "1,80 m²", "ILUMINAÇÃO": "1/10", "VENTILAÇÃO": "1/16", "PÉ-DIREITO": "2,20 m", "OBS.": "1-2-7"},
    {"AMBIENTE": "Garagem", "CÍRCULO INSCRITO": "2,20 m", "ÁREA MÍNIMA": "9,00 m²", "ILUMINAÇÃO": "1/14", "VENTILAÇÃO": "1/24", "PÉ-DIREITO": "2,20 m", "OBS.": "7"},
    {"AMBIENTE": "Escada", "CÍRCULO INSCRITO": "0,80 m", "ÁREA MÍNIMA": "–", "ILUMINAÇÃO": "–", "VENTILAÇÃO": "–", "PÉ-DIREITO": "2,10 m", "OBS.": "8-11-12-13"},
]

QUADRO_OBS = [
    "Tolera-se iluminação e ventilação zenital.",
    "Admite-se ventilação mecânica ou indireta nos casos permitidos.",
    "Banheiro não pode comunicar-se diretamente com cozinha ou sala de jantar.",
    "Corredores com mais de 5,00m devem ter largura mínima de 1,00m.",
    "Corredores com mais de 10,00m exigem ventilação mínima proporcional.",
    "Área de porta com veneziana pode ser computada como ventilação.",
    "Escadas devem ser de material incombustível ou tratado.",
    "Patamar obrigatório quando houver mudança de direção ou altura superior a 2,90m.",
    "Largura mínima do degrau: 0,25m.",
    "Altura máxima do degrau: 0,19m.",
]

PERMEABILIDADE_ROWS = [
    ("Grama", "100%"),
    ("Brita solta / terra batida", "100%"),
    ("Piso drenante", "90%"),
    ("Bloco de concreto vazado (\"piso verde\")", "60%"),
    ("Pedra portuguesa / intertravado", "25%"),
]

DICAS_VALIOSAS = [
    (
        "Passeios (calçadas)",
        "Não há, na legislação municipal, uma medida única e fixa para a largura dos passeios. Quando existir, deve-se adotar o padrão definido no projeto aprovado do loteamento e/ou nas diretrizes urbanísticas da via; na ausência dessa previsão, utiliza-se como referência o passeio já implantado no logradouro, garantindo continuidade e alinhamento, sendo a análise do licenciamento voltada a confirmar que a proposta não avança sobre a área pública.",
    ),
    (
        "Piscinas",
        "Se for construída uma piscina, ela não é computada como área construída e, por isso, não entra no cálculo da Taxa de Ocupação (TO). Porém, para a Taxa de Permeabilidade (TP), a piscina é considerada área impermeável, reduzindo a área permeável do lote. Além disso, conforme o Art. 144, piscinas, espelhos d’água, caixas d’água, cisternas e tanques devem manter afastamento mínimo de 0,50 m de todas as divisas do terreno e sempre ser computados como área impermeável no cálculo da TP.",
    ),
]


class _ReportPDF(FPDF):
    def header(self) -> None:
        self.set_font("Helvetica", "B", 19)
        self.set_text_color(26, 43, 76)
        self.cell(0, 10, _sanitize("RELATÓRIO URBANÍSTICO"), new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(110, 110, 110)
        self.cell(0, 5, _sanitize("Viabilidade Fácil / Viabilidade Urbana Sobral"), new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_draw_color(220, 224, 230)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(5)
        self.set_text_color(0, 0, 0)

    def footer(self) -> None:
        self.set_y(-10)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5, _sanitize(f"Página {self.page_no()}"), align="C")


def _sanitize(text: Any) -> str:
    return str(text).encode("latin-1", "replace").decode("latin-1")


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


def _fmt_num(value: Any, dec: int = 2) -> str:
    number = _safe_float(value)
    if number is None:
        return "—"
    return f"{number:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_area(value: Any) -> str:
    txt = _fmt_num(value)
    return f"{txt} m²" if txt != "—" else txt


def _fmt_m(value: Any) -> str:
    txt = _fmt_num(value)
    return f"{txt} m" if txt != "—" else txt


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
    parsed = _safe_float(value)
    if parsed is None:
        return None
    return parsed * 100.0 if 0 <= parsed <= 1.0 else parsed


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
            out.append(
                {
                    "title": item.get("title") or item.get("titulo") or "Figura",
                    "caption": item.get("caption") or item.get("legenda") or "",
                    "url": _build_public_storage_url(str(item.get("bucket")), str(item.get("path"))),
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



def _full_width(pdf: _ReportPDF) -> float:
    return max(10.0, pdf.w - pdf.l_margin - pdf.r_margin)

def _ensure_space(pdf: _ReportPDF, needed_h: float) -> None:
    if pdf.get_y() + needed_h > pdf.h - pdf.b_margin:
        pdf.add_page()


def _section_title(pdf: _ReportPDF, title: str) -> None:
    _ensure_space(pdf, 12)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(26, 43, 76)
    pdf.cell(0, 8, _sanitize(title), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)


def _sub_title(pdf: _ReportPDF, title: str) -> None:
    _ensure_space(pdf, 10)
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(26, 43, 76)
    pdf.multi_cell(0, 7, _sanitize(title))
    pdf.set_text_color(0, 0, 0)


def _paragraph(pdf: _ReportPDF, text: str, *, bold: bool = False, color: tuple[int, int, int] | None = None) -> None:
    _ensure_space(pdf, 8)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B" if bold else "", 11)
    if color:
        pdf.set_text_color(*color)
    pdf.multi_cell(_full_width(pdf), 6, _sanitize(text))
    pdf.set_text_color(0, 0, 0)


def _bullet_list(pdf: _ReportPDF, items: List[str]) -> None:
    for item in items:
        _ensure_space(pdf, 7)
        pdf.set_x(pdf.l_margin + 4)
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 6, _sanitize(f"• {item}"))


def _meta_header(pdf: _ReportPDF, calc: Dict[str, Any], session_state: Dict[str, Any]) -> None:
    rule = calc.get("rule") or {}
    area = _safe_float(calc.get("lot_area_m2") or session_state.get("lot_area_m2"))
    front = _safe_float(session_state.get("lot_front_m") or calc.get("lot_front_m"))
    depth = _safe_float(session_state.get("lot_depth_m") or calc.get("lot_depth_m"))
    zone = calc.get("zone") or calc.get("zone_sigla") or "—"
    via = calc.get("via_nome") or calc.get("street_name") or "—"
    via_tipo = calc.get("via_tipo") or calc.get("street_type") or "—"
    uso = calc.get("use_type_code") or "RES_UNI"
    is_corner = bool(session_state.get("lot_is_corner") or calc.get("lot_is_corner"))
    tipo_lote = "Esquina" if is_corner else "Meio de quadra"

    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 7, _sanitize("Residencial Unifamiliar" if str(uso).startswith("RES_UNI") else str(uso)), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 11)
    line = f"Terreno: {_fmt_area(area)}    Dimensões: {_fmt_m(front)} x {_fmt_m(depth)}    Zona: {zone}    Tipo: {tipo_lote}"
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(_full_width(pdf), 6, _sanitize(line))
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(110, 110, 110)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(_full_width(pdf), 5.5, _sanitize(f"Via: {via} | Tipo de via: {via_tipo} | Uso: {uso}"))
    if rule.get("subzona") or rule.get("subzone_code"):
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(_full_width(pdf), 5.5, _sanitize(f"Subzona: {rule.get('subzona') or rule.get('subzone_code')}"))
    pdf.set_text_color(0, 0, 0)


def _simple_table(pdf: _ReportPDF, headers: List[str], rows: List[List[str]], widths: List[float], *, header_fill: tuple[int, int, int] = (242, 245, 248), font_size: int = 10) -> None:
    line_h = 6.2
    total_w = sum(widths)
    if total_w <= 0:
        return

    def _row_height(row: List[str]) -> float:
        max_lines = 1
        for idx, text in enumerate(row):
            col_w = max(4.0, widths[idx] - 2)
            lines = pdf.multi_cell(col_w, line_h, _sanitize(text), dry_run=True, output="LINES")
            max_lines = max(max_lines, len(lines))
        return max_lines * line_h

    # header
    _ensure_space(pdf, line_h + 4)
    pdf.set_font("Helvetica", "B", font_size)
    pdf.set_fill_color(*header_fill)
    x0 = pdf.l_margin
    y0 = pdf.get_y()
    header_h = _row_height(headers)
    x = x0
    for idx, head in enumerate(headers):
        w = widths[idx]
        pdf.rect(x, y0, w, header_h)
        pdf.set_xy(x + 1, y0 + 1)
        pdf.multi_cell(w - 2, line_h - 0.5, _sanitize(head), border=0)
        x += w
    pdf.set_y(y0 + header_h)

    pdf.set_font("Helvetica", "", font_size)
    for row in rows:
        row_h = _row_height(row)
        _ensure_space(pdf, row_h + 1)
        x = pdf.l_margin
        y = pdf.get_y()
        for idx, cell in enumerate(row):
            w = widths[idx]
            pdf.rect(x, y, w, row_h)
            pdf.set_xy(x + 1, y + 1)
            pdf.multi_cell(w - 2, line_h - 0.5, _sanitize(cell), border=0)
            x += w
        pdf.set_y(y + row_h)


def _render_quadro_tecnico(pdf: _ReportPDF) -> None:
    _section_title(pdf, "QUADRO TÉCNICO – PARÂMETROS DOS AMBIENTES")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 90, 90)
    pdf.multi_cell(_full_width(pdf), 5.5, _sanitize("Lei Complementar nº 90/2023 – Anexo II"))
    pdf.set_text_color(0, 0, 0)
    headers = ["AMBIENTE", "CÍRCULO INSCRITO", "ÁREA MÍNIMA", "ILUMINAÇÃO", "VENTILAÇÃO", "PÉ-DIREITO", "OBS."]
    rows = [[r[h] for h in headers] for r in QUADRO_ROWS]
    widths = [44, 28, 26, 23, 23, 24, 18]
    _simple_table(pdf, headers, rows, widths, font_size=9)
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 11)
    pdf.multi_cell(_full_width(pdf), 6, _sanitize("Observações aplicáveis (Anexo II – LC 90/2023)"))
    pdf.set_font("Helvetica", "", 10)
    _bullet_list(pdf, QUADRO_OBS)


def _render_permeabilidade_table(pdf: _ReportPDF) -> None:
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 11)
    pdf.multi_cell(0, 6, _sanitize("Tipos de piso e quanto contam como permeáveis (Lei Complementar nº 90/2023 – Art. 108)"))
    headers = ["Tipo de Piso", "Percentual considerado permeável"]
    rows = [[a, b] for a, b in PERMEABILIDADE_ROWS]
    widths = [110, 70]
    _simple_table(pdf, headers, rows, widths, font_size=10)
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5.5, _sanitize("Isso significa que nem todo piso externo conta 100% como permeável."))


def _render_dicas_valiosas(pdf: _ReportPDF) -> None:
    _section_title(pdf, "DICAS VALIOSAS")
    for titulo, texto in DICAS_VALIOSAS:
        pdf.set_font("Helvetica", "B", 11)
        pdf.multi_cell(_full_width(pdf), 6, _sanitize(f"{titulo}:"))
        pdf.set_font("Helvetica", "", 10.5)
        pdf.multi_cell(_full_width(pdf), 5.8, _sanitize(texto))
        pdf.ln(1)


def _render_figuras(pdf: _ReportPDF, figures: List[Dict[str, Any]]) -> None:
    if not figures:
        return
    _section_title(pdf, "FIGURAS ANEXAS (ANEXO V)")
    temp_files: List[str] = []
    try:
        for figure in figures:
            title = _safe_str(figure.get("title"), "Figura")
            caption = _safe_str(figure.get("caption"), "")
            url = figure.get("url")
            _sub_title(pdf, title)
            if caption and caption != title:
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(90, 90, 90)
                pdf.multi_cell(_full_width(pdf), 5.2, _sanitize(caption))
                pdf.set_text_color(0, 0, 0)
            if not url:
                pdf.set_font("Helvetica", "", 10)
                pdf.multi_cell(_full_width(pdf), 5.5, _sanitize("Figura sem URL pública disponível."))
                continue
            temp = _download_temp_image(url)
            if not temp:
                pdf.set_font("Helvetica", "", 10)
                pdf.multi_cell(_full_width(pdf), 5.5, _sanitize("Não foi possível carregar esta figura no PDF."))
                continue
            temp_files.append(temp)
            max_w = pdf.w - pdf.l_margin - pdf.r_margin
            max_h = 165
            img_w, img_h = _fit_image_size(temp, max_w, max_h)
            _ensure_space(pdf, img_h + 8)
            y = pdf.get_y()
            try:
                pdf.image(temp, x=pdf.l_margin, y=y, w=img_w, h=img_h)
                pdf.set_y(y + img_h + 4)
            except Exception:
                pdf.set_font("Helvetica", "", 10)
                pdf.multi_cell(_full_width(pdf), 5.5, _sanitize("Não foi possível renderizar esta figura no PDF."))
    finally:
        for path in temp_files:
            try:
                os.remove(path)
            except Exception:
                pass


def _render_identificacao_e_indices(pdf: _ReportPDF, calc: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
    rule = calc.get("rule") or {}
    area = _safe_float(calc.get("lot_area_m2") or session_state.get("lot_area_m2")) or 0.0
    front = _safe_float(session_state.get("lot_front_m") or calc.get("lot_front_m")) or 0.0
    depth = _safe_float(session_state.get("lot_depth_m") or calc.get("lot_depth_m")) or 0.0
    is_irregular = bool(session_state.get("lot_is_irregular"))

    to_max = _to_pct(rule, "to_max_pct", "to_max")
    tp_min = _to_pct(rule, "tp_min_pct", "tp_min")
    ia_max = _safe_float(rule.get("ia_max"))
    rec_fr = _safe_float(rule.get("recuo_frontal_m")) or 0.0
    rec_lat = _safe_float(rule.get("recuo_lateral_m")) or 0.0
    rec_fun = _safe_float(rule.get("recuo_fundos_m")) or 0.0
    gabarito = rule.get("gabarito_m")

    a_to = area * (to_max / 100.0) if to_max is not None else None
    a_perm_min = area * (tp_min / 100.0) if tp_min is not None else None
    a_total = area * ia_max if ia_max is not None else None
    w_util = front - 2 * rec_lat
    d_util = depth - rec_fr - rec_fun
    a_recuos = (w_util * d_util) if (w_util > 0 and d_util > 0) else None
    a_op1_max = min(a_to, a_recuos) if (a_to is not None and a_recuos is not None) else None
    a_fundo = (front * (depth - rec_fun)) if (front > 0 and depth > rec_fun) else None
    a_op2_max = min(a_to, a_fundo) if (a_to is not None and a_fundo is not None) else a_to

    user_ground = _safe_float(session_state.get("built_ground_m2"))
    a_adotada = None
    if user_ground is not None and user_ground > 0:
        teto = a_op2_max or a_op1_max or a_to
        a_adotada = min(user_ground, teto) if teto is not None else user_ground

    def _tp_scenario(a_terreo: float | None) -> Optional[tuple[float, float]]:
        if a_terreo is None or a_perm_min is None:
            return None
        a_rest = area - a_terreo
        a_imperm = a_rest - a_perm_min
        return a_rest, a_imperm

    _section_title(pdf, "1. QUANTO POSSO OCUPAR NO CHÃO?")
    if to_max is None or a_to is None:
        _paragraph(pdf, "Sem TO máxima cadastrada para esta zona/uso.")
    else:
        _paragraph(pdf, f"A zona permite ocupar até { _fmt_pct(to_max) } do terreno no térreo.")
        _paragraph(pdf, f"{_fmt_area(area)} x {_fmt_pct(to_max)} = {_fmt_area(a_to)}", bold=True)
        _paragraph(pdf, "Esse é o limite máximo permitido pela Taxa de Ocupação (TO).")
        if a_adotada is not None:
            if user_ground is not None and a_adotada < user_ground:
                _paragraph(pdf, f"Você informou {_fmt_area(user_ground)} no térreo, mas o máximo permitido é {_fmt_area(a_adotada)}. Os cálculos abaixo usam o valor permitido.", color=(180, 100, 20))
            else:
                _paragraph(pdf, f"Área considerada no seu projeto (térreo): {_fmt_area(a_adotada)}.", color=(30, 120, 70))
        _paragraph(pdf, "Agora veja duas situações possíveis:")
        if not is_irregular:
            _paragraph(pdf, "Opção 1 – Respeitando os recuos padrão", bold=True)
            _bullet_list(pdf, [
                f"Frontal: {_fmt_m(rec_fr)}",
                f"Laterais: {_fmt_m(rec_lat)} cada",
                f"Fundo: {_fmt_m(rec_fun)}",
            ])
            _paragraph(pdf, f"Largura útil: {_fmt_m(front)} − {_fmt_m(rec_lat)} − {_fmt_m(rec_lat)} = {_fmt_m(w_util)}")
            _paragraph(pdf, f"Profundidade útil: {_fmt_m(depth)} − {_fmt_m(rec_fr)} − {_fmt_m(rec_fun)} = {_fmt_m(d_util)}")
            if a_recuos is not None:
                _paragraph(pdf, f"{_fmt_m(w_util)} x {_fmt_m(d_util)} = {_fmt_area(a_recuos)}", bold=True)
            if a_op1_max is not None:
                _paragraph(pdf, f"Nesse caso, mesmo podendo ocupar {_fmt_area(a_to)} pela regra da zona, o limite físico pelos recuos é {_fmt_area(a_op1_max)}.")
        else:
            _paragraph(pdf, "Terreno irregular: como o lote não é retangular, o relatório não calcula a implantação por recuos. Aqui são apresentados apenas os limites legais por TO/TP/IA. A implantação pode ser reduzida por recuos, forma do lote, alinhamento, servidões e exigências do licenciamento.")
        _paragraph(pdf, "Opção 2 – Implantação no alinhamento (Art. 112 – LC 90/2023)", bold=True)
        _paragraph(pdf, "Por se tratar de residência unifamiliar, a legislação permite zerar o recuo frontal e os recuos laterais, desde que:")
        _bullet_list(pdf, [
            "Seja respeitada a Taxa de Ocupação (TO) máxima",
            "Seja respeitada a Taxa de Permeabilidade (TP) mínima",
        ])
        _paragraph(pdf, "Nesse caso, você pode utilizar no térreo até o limite permitido pela TO.")
        _paragraph(pdf, "O recuo de fundo permanece obrigatório.")
        if a_op2_max is not None:
            _paragraph(pdf, f"Térreo máximo nesta opção: {_fmt_area(a_op2_max)}", bold=True)

    _section_title(pdf, "2. QUANTO PRECISO DEIXAR LIVRE?")
    if tp_min is None or a_perm_min is None:
        _paragraph(pdf, "Sem TP mínima cadastrada para esta zona/uso.")
    else:
        _paragraph(pdf, f"A zona exige {_fmt_pct(tp_min)} de área permeável.")
        _paragraph(pdf, f"{_fmt_area(area)} x {_fmt_pct(tp_min)} = {_fmt_area(a_perm_min)} obrigatórios permeáveis", bold=True)
        if a_adotada is not None:
            tp_user = _tp_scenario(a_adotada)
            if tp_user:
                a_rest, a_imperm = tp_user
                _paragraph(pdf, "Cenário com a área adotada para o seu projeto", bold=True)
                _paragraph(pdf, f"Se você utilizar {_fmt_area(a_adotada)} no térreo, a área restante no lote será {_fmt_area(a_rest)}.")
                _bullet_list(pdf, [
                    f"{_fmt_area(a_perm_min)} devem permitir infiltração no solo",
                    f"{_fmt_area(a_imperm)} podem receber piso impermeável",
                ])
        if a_op1_max is not None:
            tp1 = _tp_scenario(a_op1_max)
            if tp1:
                a_rest, a_imperm = tp1
                _paragraph(pdf, "Cenário pela Opção 1 (recuos padrão)", bold=True)
                _paragraph(pdf, f"Usando {_fmt_area(a_op1_max)} no térreo, sobra {_fmt_area(a_rest)} no lote.")
                _bullet_list(pdf, [
                    f"{_fmt_area(a_perm_min)} devem permitir infiltração no solo",
                    f"{_fmt_area(a_imperm)} podem receber piso impermeável",
                ])
        if a_op2_max is not None:
            tp2 = _tp_scenario(a_op2_max)
            if tp2:
                a_rest, a_imperm = tp2
                _paragraph(pdf, "Cenário pela Opção 2 (Art. 112)", bold=True)
                _paragraph(pdf, f"Usando {_fmt_area(a_op2_max)} no térreo, sobra {_fmt_area(a_rest)} no lote.")
                _bullet_list(pdf, [
                    f"{_fmt_area(a_perm_min)} devem permitir infiltração no solo",
                    f"{_fmt_area(a_imperm)} podem receber piso impermeável",
                ])
        _render_permeabilidade_table(pdf)

    _section_title(pdf, "3. POSSO CONSTRUIR MAIS ANDARES?")
    if ia_max is None or a_total is None:
        _paragraph(pdf, "Sem IA máximo cadastrado para esta zona/uso.")
    else:
        _paragraph(pdf, "Além do limite no chão, existe o limite total permitido.")
        _paragraph(pdf, f"Índice de Aproveitamento (IA): {ia_max:.2f}", bold=True)
        _paragraph(pdf, f"{_fmt_area(area)} x {ia_max:.2f} = {_fmt_area(a_total)} no total", bold=True)
        _paragraph(pdf, f"Isso significa que você pode distribuir até {_fmt_area(a_total)} somando todos os pavimentos.")
    if gabarito is not None:
        _paragraph(pdf, f"Altura máxima da zona: {_fmt_m(gabarito)}", bold=True)

    _section_title(pdf, "4. ESTACIONAMENTO")
    _paragraph(pdf, "De acordo com o Anexo IV da Lei Complementar nº 90/2023, não há previsão de quantidade mínima obrigatória de vagas para residência unifamiliar.")
    _paragraph(pdf, "A exigência de vagas aplica-se às residências multifamiliares e demais atividades listadas no Anexo IV.")

    return {
        "to_max": to_max,
        "tp_min": tp_min,
        "ia_max": ia_max,
        "a_to": a_to,
        "a_perm_min": a_perm_min,
        "a_total": a_total,
        "a_adotada": a_adotada,
    }


def build_report_payload(calc: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
    rule = calc.get("rule") or {}
    return {
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "calc": calc,
        "session_state": session_state,
        "figures": _extract_figures_from_rule(rule),
    }


def generate_report_pdf_bytes(calc: Dict[str, Any], session_state: Dict[str, Any]) -> bytes:
    payload = build_report_payload(calc, session_state)
    pdf = _ReportPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.set_margins(14, 24, 14)
    pdf.add_page()

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, _sanitize(f"Emitido em: {payload['generated_at']}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(1)

    _meta_header(pdf, calc, session_state)
    _render_identificacao_e_indices(pdf, calc, session_state)
    _render_quadro_tecnico(pdf)
    _render_dicas_valiosas(pdf)
    _render_figuras(pdf, payload.get("figures", []))

    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(_full_width(pdf), 4.5, _sanitize("Documento gerado pelo Viabilidade Fácil com base nos parâmetros urbanísticos exibidos no relatório do sistema."))
    result = pdf.output(dest="S")
    if isinstance(result, bytearray):
        return bytes(result)
    if isinstance(result, bytes):
        return result
    return result.encode("latin-1", errors="replace")
