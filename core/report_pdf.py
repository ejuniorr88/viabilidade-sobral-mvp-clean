from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.request import urlopen

from fpdf import FPDF

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None  # type: ignore


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
                    "bucket": item.get("bucket"),
                    "path": item.get("path"),
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


def _safe_ref(value: str, max_len: int = 78) -> str:
    text = str(value or "").strip().replace("\n", " ")
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _calc_unifamiliar(calc: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
    rule = calc.get("rule") or {}

    area = _safe_float(calc.get("lot_area_m2") or session_state.get("lot_area_m2")) or 0.0
    front = _safe_float(session_state.get("lot_front_m") or calc.get("lot_front_m")) or 0.0
    depth = _safe_float(session_state.get("lot_depth_m") or calc.get("lot_depth_m")) or 0.0
    built_ground = _safe_float(session_state.get("built_ground_m2") or calc.get("built_ground_m2"))
    permeable_area = _safe_float(session_state.get("permeable_area_m2") or calc.get("permeable_area_m2"))

    to_max = _to_pct(rule, "to_max_pct", "to_max")
    tp_min = _to_pct(rule, "tp_min_pct", "tp_min")
    ia_max = _safe_float(rule.get("ia_max"))
    rec_fr = _safe_float(rule.get("recuo_frontal_m")) or 0.0
    rec_lat = _safe_float(rule.get("recuo_lateral_m")) or 0.0
    rec_fun = _safe_float(rule.get("recuo_fundos_m")) or 0.0
    gabarito_m = _safe_float(rule.get("gabarito_m"))

    area_to = area * (to_max / 100.0) if to_max is not None else None
    area_perm_min = area * (tp_min / 100.0) if tp_min is not None else None
    area_total = area * ia_max if ia_max is not None else None

    largura_util = front - 2 * rec_lat
    profundidade_util = depth - rec_fr - rec_fun
    area_recuos = (largura_util * profundidade_util) if (largura_util > 0 and profundidade_util > 0) else None
    area_op1_max = min(area_to, area_recuos) if (area_to is not None and area_recuos is not None) else None

    area_fundo = (front * (depth - rec_fun)) if (front > 0 and depth > rec_fun) else None
    if area_to is not None and area_fundo is not None:
        area_op2_max = min(area_to, area_fundo)
    elif area_to is not None:
        area_op2_max = area_to
    else:
        area_op2_max = None

    area_adotada = None
    if built_ground is not None and built_ground > 0:
        teto = area_op2_max or area_op1_max or area_to
        area_adotada = min(built_ground, float(teto)) if teto is not None else built_ground

    def _tp_scenario(area_terreo: float | None) -> Optional[Tuple[float, float]]:
        if area_terreo is None or area_perm_min is None:
            return None
        area_rest = area - area_terreo
        area_imperm_max = area_rest - area_perm_min
        return area_rest, area_imperm_max

    return {
        "area": area,
        "front": front,
        "depth": depth,
        "built_ground": built_ground,
        "permeable_area": permeable_area,
        "to_max": to_max,
        "tp_min": tp_min,
        "ia_max": ia_max,
        "rec_fr": rec_fr,
        "rec_lat": rec_lat,
        "rec_fun": rec_fun,
        "gabarito_m": gabarito_m,
        "area_to": area_to,
        "area_perm_min": area_perm_min,
        "area_total": area_total,
        "largura_util": largura_util,
        "profundidade_util": profundidade_util,
        "area_recuos": area_recuos,
        "area_op1_max": area_op1_max,
        "area_op2_max": area_op2_max,
        "area_adotada": area_adotada,
        "tp_user": _tp_scenario(area_adotada),
        "tp1": _tp_scenario(area_op1_max),
        "tp2": _tp_scenario(area_op2_max),
        "is_irregular": bool(session_state.get("lot_is_irregular", False)),
        "is_corner": bool(session_state.get("lot_is_corner", False)),
    }


class _ReportPDF(FPDF):
    def header(self) -> None:
        self.set_fill_color(31, 42, 68)
        self.rect(0, 0, self.w, 22, style="F")
        self.set_xy(14, 6)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 8, _sanitize("Viabilidade Fácil"), ln=True)
        self.set_x(14)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, _sanitize("Relatório Urbanístico"), ln=True)
        self.set_text_color(20, 20, 20)
        self.ln(6)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_draw_color(220, 220, 220)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_y(-10)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(90, 90, 90)
        self.cell(0, 6, _sanitize(f"Página {self.page_no()}"), align="C")
        self.set_text_color(20, 20, 20)

    def section_heading(self, title: str) -> None:
        self.ln(3)
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(31, 42, 68)
        self.multi_cell(0, 10, _sanitize(title))
        self.set_text_color(20, 20, 20)
        self.ln(1)

    def subheading(self, title: str) -> None:
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(31, 42, 68)
        self.multi_cell(0, 7, _sanitize(title))
        self.set_text_color(20, 20, 20)
        self.ln(1)

    def paragraph(self, text: str, size: int = 11, style: str = "") -> None:
        self.set_font("Helvetica", style, size)
        self.multi_cell(0, 6.4, _sanitize(text))

    def bullet(self, text: str, size: int = 11, bullet_text: str = "•") -> None:
        x = self.get_x()
        y = self.get_y()
        self.set_font("Helvetica", "", size)
        self.cell(6, 6.2, _sanitize(bullet_text))
        self.set_xy(x + 6, y)
        self.multi_cell(0, 6.2, _sanitize(text))

    def info_box(self, text: str, fill_rgb: Tuple[int, int, int] = (243, 248, 244), text_rgb: Tuple[int, int, int] = (34, 85, 46)) -> None:
        self.set_fill_color(*fill_rgb)
        self.set_draw_color(225, 235, 228)
        self.set_text_color(*text_rgb)
        self.set_font("Helvetica", "B", 11)
        self.multi_cell(0, 8, _sanitize(text), border=1, fill=True)
        self.set_text_color(20, 20, 20)
        self.ln(1)


def _render_top_summary(pdf: _ReportPDF, calc: Dict[str, Any], session_state: Dict[str, Any], uni: Dict[str, Any]) -> None:
    rule = calc.get("rule") or {}
    zone = calc.get("zone") or calc.get("zone_sigla") or "—"
    via = calc.get("via_nome") or calc.get("street_name") or "—"
    via_tipo = calc.get("via_tipo") or calc.get("street_type") or "—"
    uso = calc.get("use_type_code") or "RES_UNI"
    tipo_lote = "Esquina" if uni["is_corner"] else "Meio de quadra"

    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(31, 42, 68)
    pdf.cell(0, 10, _sanitize("RELATÓRIO URBANÍSTICO"), ln=True)
    pdf.set_text_color(20, 20, 20)
    pdf.set_font("Helvetica", "", 13)
    pdf.cell(0, 8, _sanitize("Residencial Unifamiliar"), ln=True)
    pdf.ln(2)

    resumo_1 = (
        f"Terreno: {_fmt_num(uni['area'])} m²  Dimensões: {_fmt_num(uni['front'])} m × {_fmt_num(uni['depth'])} m  "
        f"Zona: {zone}  Tipo: {tipo_lote}"
    )
    pdf.set_font("Helvetica", "B", 11)
    pdf.multi_cell(0, 6.2, _sanitize(resumo_1))
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 5.8, _sanitize(f"Via: {via} | Tipo de via: {via_tipo} | Uso: {uso}"))
    pdf.set_text_color(20, 20, 20)
    pdf.ln(2)

    to_pct = calc.get("to_pct")
    ia = calc.get("ia")
    tp_pct = calc.get("tp_pct")
    if to_pct is not None:
        pdf.paragraph(f"TO utilizada: {_fmt_pct(to_pct)}")
    if ia is not None:
        pdf.paragraph(f"IA utilizado (considerando térreo adotado): {_fmt_num(ia)}")
    if tp_pct is not None:
        pdf.paragraph(f"TP prevista: {_fmt_pct(tp_pct)}")

    ok_to = calc.get("to_ok")
    ok_ia = calc.get("ia_ok")
    ok_tp = calc.get("tp_ok")
    if ok_to is True:
        pdf.info_box("Taxa de Ocupação dentro do permitido")
    if ok_ia is True:
        pdf.info_box("Índice de Aproveitamento dentro do permitido")
    if ok_tp is True:
        pdf.info_box("Taxa de Permeabilidade atende o mínimo")


QUADRO_TECNICO_ROWS: List[Dict[str, str]] = [
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

OBS_QUADRO = [
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


def _render_quadro_tecnico(pdf: _ReportPDF) -> None:
    pdf.section_heading("QUADRO TÉCNICO – PARÂMETROS DOS AMBIENTES")
    pdf.paragraph("(Lei Complementar nº 90/2023 – Anexo II)", size=11)
    pdf.ln(1)

    headers = ["AMBIENTE", "CÍRCULO INSCRITO", "ÁREA MÍNIMA", "ILUMINAÇÃO", "VENTILAÇÃO", "PÉ-DIREITO", "OBS."]
    widths = [44, 28, 25, 22, 22, 24, 19]
    row_h = 7.2

    pdf.set_font("Helvetica", "B", 8.3)
    pdf.set_fill_color(245, 247, 250)
    pdf.set_draw_color(220, 226, 234)
    for header, width in zip(headers, widths):
        pdf.cell(width, 8, _sanitize(header), border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 8.8)
    for row in QUADRO_TECNICO_ROWS:
        if pdf.get_y() > 252:
            pdf.add_page()
        vals = [row[h] for h in headers]
        x0 = pdf.get_x()
        y0 = pdf.get_y()
        max_h = row_h
        for value, width in zip(vals, widths):
            max_h = max(max_h, row_h * max(1, int((len(str(value)) / max(8, width / 2.4))) + 0))
        curr_x = x0
        for value, width in zip(vals, widths):
            pdf.set_xy(curr_x, y0)
            pdf.multi_cell(width, row_h, _sanitize(str(value)), border=1)
            curr_x += width
        pdf.set_xy(x0, y0 + max_h)

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.multi_cell(0, 6.2, _sanitize("Observações aplicáveis (Anexo II – LC 90/2023)"))
    pdf.set_fill_color(245, 247, 250)
    pdf.set_draw_color(230, 234, 240)
    start_x = pdf.get_x()
    start_y = pdf.get_y()
    pdf.multi_cell(0, 6.1, _sanitize("\n".join([f"- {item}" for item in OBS_QUADRO])), border=1, fill=True)
    pdf.ln(2)


def _render_dicas_valiosas(pdf: _ReportPDF) -> None:
    pdf.section_heading("Dicas Valiosas:")
    pdf.paragraph(
        "• Passeios (calçadas): Não há, na legislação municipal, uma medida única e fixa para a largura dos passeios. Quando existir, deve-se adotar o padrão definido no projeto aprovado do loteamento e/ou nas diretrizes urbanísticas da via; na ausência dessa previsão, utiliza-se como referência o passeio já implantado no logradouro, garantindo continuidade e alinhamento, sendo a análise do licenciamento voltada a confirmar que a proposta não avança sobre a área pública.",
        size=11,
    )
    pdf.ln(1)
    pdf.paragraph(
        "• Piscinas: Se for construída uma piscina, ela não é computada como área construída e, por isso, não entra no cálculo da Taxa de Ocupação (TO). Porém, para a Taxa de Permeabilidade (TP), a piscina é considerada área impermeável, reduzindo a área permeável do lote. Além disso, conforme o Art. 144, piscinas, espelhos d’água, caixas d’água, cisternas e tanques devem manter afastamento mínimo de 0,50 m de todas as divisas do terreno e sempre ser computados como área impermeável no cálculo da TP.",
        size=11,
    )
    pdf.ln(2)


def _render_section_1(pdf: _ReportPDF, uni: Dict[str, Any]) -> None:
    pdf.section_heading("1  Quanto posso ocupar no chão?")
    if uni["to_max"] is None or uni["area_to"] is None:
        pdf.paragraph("Sem TO máxima cadastrada para esta zona/uso.")
        return

    pdf.paragraph(f"A zona permite ocupar até { _fmt_pct(uni['to_max']) } do terreno no térreo.")
    pdf.paragraph(f"👉 {_fmt_num(uni['area'])} m² × {_fmt_pct(uni['to_max'])} = {_fmt_num(uni['area_to'])} m²", style="B")
    pdf.paragraph("Esse é o limite máximo permitido pela Taxa de Ocupação (TO).")

    if uni["area_adotada"] is not None:
        pdf.paragraph(f"Área considerada no seu projeto (térreo): {_fmt_num(uni['area_adotada'])} m².")

    pdf.paragraph("Agora veja duas situações possíveis:")

    if not uni["is_irregular"]:
        pdf.paragraph("✅ Opção 1 – Respeitando os recuos padrão", style="B")
        pdf.paragraph("Recuos exigidos:", style="B")
        pdf.bullet(f"Frontal: {_fmt_num(uni['rec_fr'])} m")
        pdf.bullet(f"Laterais: {_fmt_num(uni['rec_lat'])} m cada")
        pdf.bullet(f"Fundo: {_fmt_num(uni['rec_fun'])} m")
        pdf.ln(1)
        pdf.paragraph("Área interna disponível:", style="B")
        pdf.paragraph(
            f"Largura útil: {_fmt_num(uni['front'])} − {_fmt_num(uni['rec_lat'])} − {_fmt_num(uni['rec_lat'])} = {_fmt_num(uni['largura_util'])} m"
        )
        pdf.paragraph(
            f"Profundidade útil: {_fmt_num(uni['depth'])} − {_fmt_num(uni['rec_fr'])} − {_fmt_num(uni['rec_fun'])} = {_fmt_num(uni['profundidade_util'])} m"
        )
        if uni["area_recuos"] is not None:
            pdf.paragraph(f"📐 {_fmt_num(uni['largura_util'])} × {_fmt_num(uni['profundidade_util'])} = {_fmt_num(uni['area_recuos'])} m²", style="B")
        if uni["area_op1_max"] is not None:
            pdf.paragraph(
                f"Nesse caso, mesmo podendo ocupar {_fmt_num(uni['area_to'])} m² pela regra da zona, o limite físico pelos recuos é {_fmt_num(uni['area_op1_max'])} m²."
            )
    else:
        pdf.paragraph(
            "Terreno irregular: como o lote não é retangular, o relatório não calcula a implantação por recuos. Aqui são apresentados apenas os limites legais por TO/TP/IA. A implantação pode ser reduzida por recuos, forma do lote, alinhamento, servidões e exigências do licenciamento."
        )

    pdf.ln(1)
    pdf.paragraph("✅ Opção 2 – Implantação no alinhamento (Art. 112 – LC 90/2023)", style="B")
    pdf.paragraph(
        "Por se tratar de residência unifamiliar, a legislação permite zerar o recuo frontal e os recuos laterais, desde que:"
    )
    pdf.bullet("Seja respeitada a Taxa de Ocupação (TO) máxima")
    pdf.bullet("Seja respeitada a Taxa de Permeabilidade (TP) mínima")
    pdf.paragraph("Nesse caso, você pode utilizar no térreo até o limite permitido pela TO.")
    pdf.paragraph("⚠ O recuo de fundo permanece obrigatório.", style="B")
    if uni["area_op2_max"] is not None:
        pdf.paragraph(f"👉 Térreo máximo nesta opção: {_fmt_num(uni['area_op2_max'])} m²", style="B")


def _render_section_2(pdf: _ReportPDF, uni: Dict[str, Any]) -> None:
    pdf.section_heading("2  Quanto preciso deixar livre?")
    if uni["tp_min"] is None or uni["area_perm_min"] is None:
        pdf.paragraph("Sem TP mínima cadastrada para esta zona/uso.")
        return

    pdf.paragraph(f"A zona exige {_fmt_pct(uni['tp_min'])} de área permeável.")
    pdf.paragraph(f"👉 {_fmt_num(uni['area'])} m² × {_fmt_pct(uni['tp_min'])} = {_fmt_num(uni['area_perm_min'])} m² obrigatórios permeáveis", style="B")

    if uni["tp_user"] is not None and uni["area_adotada"] is not None:
        area_rest, area_imperm = uni["tp_user"]
        pdf.paragraph("✅ Cenário com a área adotada para o seu projeto", style="B")
        pdf.paragraph(f"Se você utilizar {_fmt_num(uni['area_adotada'])} m² no térreo:")
        pdf.paragraph(f"Área restante no lote: {_fmt_num(uni['area'])} m² − {_fmt_num(uni['area_adotada'])} m² = {_fmt_num(area_rest)} m²")
        pdf.bullet(f"{_fmt_num(uni['area_perm_min'])} m² devem permitir infiltração no solo")
        pdf.bullet(f"{_fmt_num(area_imperm)} m² podem receber piso impermeável")
        pdf.ln(1)

    if uni["tp1"] is not None and uni["area_op1_max"] is not None:
        area_rest, area_imperm = uni["tp1"]
        pdf.paragraph("✅ Cenário pela Opção 1 (recuos padrão)", style="B")
        pdf.paragraph(f"Se você utilizar {_fmt_num(uni['area_op1_max'])} m² no térreo:")
        pdf.paragraph(f"Área restante no lote: {_fmt_num(uni['area'])} m² − {_fmt_num(uni['area_op1_max'])} m² = {_fmt_num(area_rest)} m²")
        pdf.bullet(f"{_fmt_num(uni['area_perm_min'])} m² devem permitir infiltração no solo")
        pdf.bullet(f"{_fmt_num(area_imperm)} m² podem receber piso impermeável")
        pdf.ln(1)

    if uni["tp2"] is not None and uni["area_op2_max"] is not None:
        area_rest, area_imperm = uni["tp2"]
        pdf.paragraph("✅ Cenário pela Opção 2 (Art. 112)", style="B")
        pdf.paragraph(f"Se você utilizar {_fmt_num(uni['area_op2_max'])} m² no térreo:")
        pdf.paragraph(f"Área restante no lote: {_fmt_num(uni['area'])} m² − {_fmt_num(uni['area_op2_max'])} m² = {_fmt_num(area_rest)} m²")
        pdf.bullet(f"{_fmt_num(uni['area_perm_min'])} m² devem permitir infiltração no solo")
        pdf.bullet(f"{_fmt_num(area_imperm)} m² podem receber piso impermeável")
        pdf.ln(1)

    pdf.paragraph("Tipos de piso e quanto contam como permeáveis (Lei Complementar nº 90/2023 – Art. 108)", style="B")
    rows = [
        ("Grama", "100%"),
        ("Brita solta / terra batida", "100%"),
        ("Piso drenante", "90%"),
        ("Bloco de concreto vazado (\"piso verde\")", "60%"),
        ("Pedra portuguesa / intertravado", "25%"),
    ]
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(245, 247, 250)
    pdf.cell(110, 8, _sanitize("Tipo de Piso"), border=1, fill=True)
    pdf.cell(70, 8, _sanitize("Percentual considerado permeável"), border=1, fill=True, ln=True)
    pdf.set_font("Helvetica", "", 10)
    for a, b in rows:
        pdf.cell(110, 8, _sanitize(a), border=1)
        pdf.cell(70, 8, _sanitize(b), border=1, ln=True)
    pdf.ln(1)
    pdf.paragraph("Isso significa que nem todo piso “externo” conta 100% como permeável.")


def _render_section_3(pdf: _ReportPDF, uni: Dict[str, Any]) -> None:
    pdf.section_heading("3  Posso construir mais andares?")
    if uni["ia_max"] is None or uni["area_total"] is None:
        pdf.paragraph("Sem IA máximo cadastrado para esta zona/uso.")
    else:
        pdf.paragraph("Além do limite no chão, existe o limite total permitido.")
        pdf.paragraph(f"Índice de Aproveitamento (IA): {uni['ia_max']:.2f}", style="B")
        pdf.paragraph(f"👉 {_fmt_num(uni['area'])} m² × {uni['ia_max']:.2f} = {_fmt_num(uni['area_total'])} m² no total", style="B")
        pdf.paragraph(f"Isso significa que você pode distribuir até {_fmt_num(uni['area_total'])} m² somando todos os pavimentos.")
    if uni["gabarito_m"] is not None:
        pdf.paragraph(f"Altura máxima da zona: {_fmt_num(uni['gabarito_m'])} m", style="B")


def _render_section_4(pdf: _ReportPDF) -> None:
    pdf.section_heading("4  Estacionamento")
    pdf.paragraph(
        "De acordo com o Anexo IV da Lei Complementar nº 90/2023, não há previsão de quantidade mínima obrigatória de vagas para residência unifamiliar."
    )
    pdf.paragraph(
        "A exigência de vagas aplica-se às residências multifamiliares e demais atividades listadas no Anexo IV."
    )


def _image_dimensions(path: str, max_w: float, max_h: float) -> Tuple[float, float]:
    if Image is None:
        return max_w, min(max_h, max_w * 0.75)
    try:
        with Image.open(path) as img:
            w, h = img.size
        if w <= 0 or h <= 0:
            return max_w, min(max_h, max_w * 0.75)
        scale = min(max_w / w, max_h / h)
        return w * scale, h * scale
    except Exception:
        return max_w, min(max_h, max_w * 0.75)


def _render_figures(pdf: _ReportPDF, figures: List[Dict[str, Any]]) -> None:
    if not figures:
        return

    temp_files: List[str] = []
    try:
        for i in range(0, len(figures), 2):
            pair = figures[i : i + 2]
            pdf.add_page(orientation="L")
            pdf.section_heading("Figuras anexas (Anexo V)")

            top_y = pdf.get_y()
            page_w = pdf.w - pdf.l_margin - pdf.r_margin
            gap = 8
            block_w = (page_w - gap) / 2 if len(pair) == 2 else page_w
            x_positions = [pdf.l_margin, pdf.l_margin + block_w + gap]

            for idx, fig in enumerate(pair):
                x = x_positions[idx]
                y = top_y
                title = _safe_str(fig.get("title"), "Figura")
                caption = _safe_str(fig.get("caption"), "")
                url = fig.get("url")
                pdf.set_xy(x, y)
                pdf.set_font("Helvetica", "B", 11)
                pdf.multi_cell(block_w, 6.2, _sanitize(title))
                pdf.set_x(x)
                if caption and caption != "—":
                    pdf.set_font("Helvetica", "", 9)
                    pdf.multi_cell(block_w, 5.2, _sanitize(caption))
                ref_y = pdf.get_y()

                if url:
                    tmp_path = _download_temp_image(url)
                    if tmp_path:
                        temp_files.append(tmp_path)
                        max_h = pdf.h - ref_y - 20
                        draw_w, draw_h = _image_dimensions(tmp_path, block_w, max_h)
                        draw_x = x + max(0, (block_w - draw_w) / 2)
                        pdf.image(tmp_path, x=draw_x, y=ref_y + 2, w=draw_w, h=draw_h)
                    else:
                        pdf.set_xy(x, ref_y + 2)
                        pdf.set_font("Helvetica", "", 9)
                        ref = _safe_ref(url or f"{fig.get('bucket')}/{fig.get('path')}")
                        pdf.multi_cell(block_w, 5.2, _sanitize(f"Não foi possível carregar a figura: {ref}"), border=1)
                else:
                    pdf.set_xy(x, ref_y + 2)
                    pdf.set_font("Helvetica", "", 9)
                    ref = _safe_ref(f"{fig.get('bucket')}/{fig.get('path')}")
                    pdf.multi_cell(block_w, 5.2, _sanitize(f"Figura sem URL pública disponível: {ref}"), border=1)
    finally:
        for path in temp_files:
            try:
                os.remove(path)
            except Exception:
                pass


def _render_unifamiliar_report(pdf: _ReportPDF, calc: Dict[str, Any], session_state: Dict[str, Any]) -> None:
    uni = _calc_unifamiliar(calc, session_state)
    _render_top_summary(pdf, calc, session_state, uni)
    _render_section_1(pdf, uni)
    _render_section_2(pdf, uni)
    _render_section_3(pdf, uni)
    _render_section_4(pdf)
    _render_quadro_tecnico(pdf)
    _render_dicas_valiosas(pdf)
    _render_figures(pdf, _extract_figures_from_rule(calc.get("rule") or {}))


def _render_generic_report(pdf: _ReportPDF, calc: Dict[str, Any], session_state: Dict[str, Any]) -> None:
    rule = calc.get("rule") or {}
    zone = calc.get("zone") or calc.get("zone_sigla") or "—"
    via = calc.get("via_nome") or calc.get("street_name") or "—"
    via_tipo = calc.get("via_tipo") or calc.get("street_type") or "—"
    uso = calc.get("use_type_code") or "—"
    lot_area = _safe_float(calc.get("lot_area_m2") or session_state.get("lot_area_m2"))

    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(31, 42, 68)
    pdf.cell(0, 10, _sanitize("RELATÓRIO URBANÍSTICO"), ln=True)
    pdf.set_text_color(20, 20, 20)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 7, _sanitize(_safe_str(uso)), ln=True)
    pdf.ln(2)
    pdf.paragraph(f"Zona: {zone}")
    pdf.paragraph(f"Via: {via}")
    pdf.paragraph(f"Tipo de via: {via_tipo}")
    pdf.paragraph(f"Área do terreno: {_fmt_num(lot_area)} m²")
    pdf.ln(2)
    pdf.subheading("Parâmetros urbanísticos")
    pdf.paragraph(f"TO máxima: {_fmt_pct(_to_pct(rule, 'to_max_pct', 'to_max'))}")
    pdf.paragraph(f"TP mínima: {_fmt_pct(_to_pct(rule, 'tp_min_pct', 'tp_min'))}")
    pdf.paragraph(f"IA máximo: {_fmt_num(rule.get('ia_max'))}")
    pdf.paragraph(f"Recuo frontal: {_fmt_num(rule.get('recuo_frontal_m'))} m")
    pdf.paragraph(f"Recuo lateral: {_fmt_num(rule.get('recuo_lateral_m'))} m")
    pdf.paragraph(f"Recuo fundos: {_fmt_num(rule.get('recuo_fundos_m'))} m")
    pdf.paragraph(f"Gabarito: {_fmt_num(rule.get('gabarito_m'))} m")
    pdf.ln(2)
    _render_figures(pdf, _extract_figures_from_rule(rule))


def generate_report_pdf_bytes(calc: Dict[str, Any], session_state: Dict[str, Any]) -> bytes:
    pdf = _ReportPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_margins(14, 28, 14)
    pdf.add_page()

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 6, _sanitize(f"Emitido em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"), ln=True)
    pdf.set_text_color(20, 20, 20)
    pdf.ln(2)

    uso = str(calc.get("use_type_code") or "")
    if uso == "RES_UNI":
        _render_unifamiliar_report(pdf, calc, session_state)
    else:
        _render_generic_report(pdf, calc, session_state)

    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(110, 110, 110)
    pdf.multi_cell(
        0,
        4.5,
        _sanitize(
            "Documento gerado pelo Viabilidade Fácil. O PDF foi estruturado para acompanhar a leitura do relatório exibido no sistema, preservando as informações principais, quadro técnico, observações e figuras anexas."
        ),
    )
    pdf.set_text_color(20, 20, 20)

    result = pdf.output(dest="S")
    if isinstance(result, bytearray):
        return bytes(result)
    if isinstance(result, bytes):
        return result
    return result.encode("latin-1", errors="replace")
