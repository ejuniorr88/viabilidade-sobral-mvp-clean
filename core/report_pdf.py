from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from datetime import datetime
from html import escape as _html_escape
from ui.relatorio_blocks.dicas_valiosas import get_dicas_valiosas
from ui.relatorio_blocks.figuras_anexo_v import filter_figuras_by_lot_type
from .zone_descriptions import fetch_zone_description
from typing import Any, Dict, List, Optional, Sequence
from urllib.request import urlopen

from fpdf import FPDF

try:
    from weasyprint import HTML
except Exception:  # pragma: no cover
    HTML = None

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
    {"AMBIENTE": "Area de servico", "CIRCULO INSCRITO": "1,20 m", "AREA MINIMA": "1,80 m²", "ILUMINACAO": "1/10", "VENTILACAO": "1/16", "PE-DIREITO": "2,20 m", "OBS.": "1-2-7"},
    {"AMBIENTE": "Garagem", "CIRCULO INSCRITO": "2,20 m", "AREA MINIMA": "9,00 m²", "ILUMINACAO": "1/14", "VENTILACAO": "1/24", "PE-DIREITO": "2,20 m", "OBS.": "7"},
    {"AMBIENTE": "Escada", "CIRCULO INSCRITO": "0,80 m", "AREA MINIMA": "-", "ILUMINACAO": "-", "VENTILACAO": "-", "PE-DIREITO": "2,10 m", "OBS.": "8-11-12-13"},
]

QUADRO_OBS = [
    "Tolera-se iluminacao e ventilacao zenital.",
    "Admite-se ventilacao mecanica ou indireta nos casos permitidos.",
    "Banheiro nao pode comunicar-se diretamente com cozinha ou sala de jantar.",
    "Corredores com mais de 5,00 m devem ter largura minima de 1,00 m.",
    "Corredores com mais de 10,00 m exigem ventilacao minima proporcional.",
    "Area de porta com veneziana pode ser computada como ventilacao.",
    "Escadas devem ser de material incombustivel ou tratado.",
    "Patamar obrigatorio quando houver mudanca de direcao ou altura superior a 2,90 m.",
    "Largura minima do degrau: 0,25 m.",
    "Altura maxima do degrau: 0,19 m.",
]

PERMEABILIDADE_ROWS = [
    ("Grama", "100%"),
    ("Brita solta / terra batida", "100%"),
    ("Piso drenante", "90%"),
    ("Bloco de concreto vazado (piso verde)", "60%"),
    ("Pedra portuguesa / intertravado", "25%"),
]

DICAS_VALIOSAS = [
    (
        "Passeios (calcadas)",
        "Nao ha, na legislacao municipal, uma medida unica e fixa para a largura dos passeios. Quando existir, deve-se adotar o padrao definido no projeto aprovado do loteamento e/ou nas diretrizes urbanisticas da via; na ausencia dessa previsao, utiliza-se como referencia o passeio ja implantado no logradouro, garantindo continuidade e alinhamento, sendo a analise do licenciamento voltada a confirmar que a proposta nao avanca sobre a area publica.",
    ),
    (
        "Piscinas",
        "Se for construida uma piscina, ela nao e computada como area construida e, por isso, nao entra no calculo da Taxa de Ocupacao (TO). Porem, para a Taxa de Permeabilidade (TP), a piscina e considerada area impermeavel, reduzindo a area permeavel do lote. Alem disso, conforme o Art. 144, piscinas, espelhos d'agua, caixas d'agua, cisternas e tanques devem manter afastamento minimo de 0,50 m de todas as divisas do terreno e sempre ser computados como area impermeavel no calculo da TP.",
    ),
]


class _ReportPDF(FPDF):
    def rounded_rect(self, x: float, y: float, w: float, h: float, r: float = 0, style: str = "") -> None:
        # Compatibilidade com versões do fpdf/fpdf2 que não expõem rounded_rect.
        rect_fn = getattr(super(), "rounded_rect", None)
        if callable(rect_fn):
            rect_fn(x, y, w, h, r, style=style)
            return
        self.rect(x, y, w, h, style=style)

    def header(self) -> None:
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(24, 41, 74)
        self.cell(0, 9, _sanitize("RELATORIO URBANISTICO"), new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(105, 105, 105)
        self.cell(0, 5, _sanitize("Viabilidade Facil / Viabilidade Urbana Sobral"), new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_draw_color(220, 224, 230)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(5)
        self.set_text_color(0, 0, 0)

    def footer(self) -> None:
        self.set_y(-10)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5, _sanitize(f"Pagina {self.page_no()}"), align="C")


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


def _section_title(pdf: _ReportPDF, title: str, *, small: bool = False) -> None:
    _ensure_space(pdf, 12)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 13 if small else 16)
    pdf.set_text_color(24, 41, 74)
    pdf.multi_cell(_full_width(pdf), 7, _sanitize(title))
    pdf.set_text_color(0, 0, 0)


def _paragraph(pdf: _ReportPDF, text: str, *, bold: bool = False, color: tuple[int, int, int] | None = None, h: float = 5.7) -> None:
    _ensure_space(pdf, h + 2)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B" if bold else "", 10.5)
    if color:
        pdf.set_text_color(*color)
    pdf.multi_cell(_full_width(pdf), h, _sanitize(text))
    pdf.set_text_color(0, 0, 0)


def _bullet_list(pdf: _ReportPDF, items: Sequence[str]) -> None:
    for item in items:
        _ensure_space(pdf, 6.2)
        pdf.set_x(pdf.l_margin + 3)
        pdf.set_font("Helvetica", "", 10.3)
        pdf.multi_cell(_full_width(pdf) - 3, 5.6, _sanitize(f"- {item}"))


def _key_value_row(pdf: _ReportPDF, pairs: Sequence[tuple[str, str]], widths: Sequence[float]) -> None:
    line_h = 5.0
    row_h = 11.0
    _ensure_space(pdf, row_h + 1)
    x = pdf.l_margin
    y = pdf.get_y()
    for idx, (label, value) in enumerate(pairs):
        w = widths[idx]
        pdf.set_fill_color(247, 249, 252)
        pdf.set_draw_color(224, 228, 234)
        pdf.rounded_rect(x, y, w, row_h, 1.5, style="DF")
        pdf.set_xy(x + 2, y + 1.4)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(w - 4, 3.5, _sanitize(label))
        pdf.set_xy(x + 2, y + 5.4)
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(w - 4, line_h, _sanitize(value), border=0)
        x += w + 2.5
    pdf.set_y(y + row_h + 2.5)


def _simple_table(pdf: _ReportPDF, headers: List[str], rows: List[List[str]], widths: List[float], *, font_size: int = 9, line_h: float = 5.6) -> None:
    total_w = sum(widths)
    if total_w <= 0:
        return

    def row_height(row: List[str], font_style: str = "") -> float:
        pdf.set_font("Helvetica", font_style, font_size)
        max_lines = 1
        for idx, text in enumerate(row):
            col_w = max(4.0, widths[idx] - 2.0)
            lines = pdf.multi_cell(col_w, line_h, _sanitize(text), dry_run=True, output="LINES")
            max_lines = max(max_lines, len(lines))
        return max_lines * line_h + 2.0

    header_h = row_height(headers, "B")
    _ensure_space(pdf, header_h + 3)
    x = pdf.l_margin
    y = pdf.get_y()
    pdf.set_fill_color(245, 247, 250)
    pdf.set_draw_color(220, 224, 230)
    pdf.set_font("Helvetica", "B", font_size)
    for idx, head in enumerate(headers):
        w = widths[idx]
        pdf.rect(x, y, w, header_h, style="DF")
        pdf.set_xy(x + 1.2, y + 1.0)
        pdf.multi_cell(w - 2.4, line_h, _sanitize(head), border=0)
        x += w
    pdf.set_y(y + header_h)

    fill_toggle = False
    for row in rows:
        this_h = row_height(row)
        _ensure_space(pdf, this_h + 1)
        x = pdf.l_margin
        y = pdf.get_y()
        if fill_toggle:
            pdf.set_fill_color(252, 253, 254)
        else:
            pdf.set_fill_color(255, 255, 255)
        fill_toggle = not fill_toggle
        pdf.set_font("Helvetica", "", font_size)
        for idx, text in enumerate(row):
            w = widths[idx]
            pdf.rect(x, y, w, this_h, style="DF")
            pdf.set_xy(x + 1.2, y + 1.0)
            pdf.multi_cell(w - 2.4, line_h, _sanitize(text), border=0)
            x += w
        pdf.set_y(y + this_h)


def _status_box(pdf: _ReportPDF, text: str, ok: bool) -> None:
    _ensure_space(pdf, 10)
    y = pdf.get_y()
    x = pdf.l_margin
    w = _full_width(pdf)
    pdf.set_draw_color(220, 224, 230)
    if ok:
        pdf.set_fill_color(231, 245, 236)
        pdf.set_text_color(27, 112, 61)
    else:
        pdf.set_fill_color(252, 238, 238)
        pdf.set_text_color(153, 52, 52)
    pdf.rounded_rect(x, y, w, 8.5, 1.4, style="DF")
    pdf.set_xy(x + 3, y + 2.2)
    pdf.set_font("Helvetica", "B", 10.5)
    prefix = "OK - " if ok else "ATENCAO - "
    pdf.cell(w - 6, 4.0, _sanitize(prefix + text))
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(y + 11)


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


def _extract_context(calc: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
    rule = calc.get("rule") or {}
    area = _pick_number(calc.get("lot_area_m2"), session_state.get("lot_area_m2"), session_state.get("lot_area_input_m2"), calc.get("lot_area_input_m2"))
    front = _pick_number(
        session_state.get("lot_front_m"), calc.get("lot_front_m"),
        session_state.get("lot_testada_m"), calc.get("lot_testada_m"),
        session_state.get("testada_m"), calc.get("testada_m"),
    )
    depth = _pick_number(
        session_state.get("lot_depth_m"), calc.get("lot_depth_m"),
        session_state.get("lot_profundidade_m"), calc.get("lot_profundidade_m"),
        session_state.get("profundidade_m"), calc.get("profundidade_m"),
    )
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

    tipo_lote = "Esquina" if is_corner else "Meio de quadra"
    zone = _pick_text(calc.get("zone"), calc.get("zone_sigla"), rule.get("zone_sigla"))
    via = _pick_text(calc.get("via_nome"), calc.get("street_name"), default="-")
    via_tipo = _pick_text(calc.get("via_tipo"), calc.get("street_type"), default="-")
    uso = _pick_text(calc.get("use_type_code"), default="RES_UNI")
    subzona = _pick_text(rule.get("subzona"), rule.get("subzone_code"), default="-")

    zone_sigla = _pick_text(calc.get("zone_sigla"), zone)
    subzone_code = _pick_text(calc.get("subzone_code"), rule.get("subzone_code"), default="PADRAO")
    zone_label = _pick_text(calc.get("zone_label_raw"), zone)
    zone_desc = _fetch_zone_description(
        zone_sigla=zone_sigla,
        subzone_code=subzone_code,
        zone_label=zone_label,
    )
    zone_class, via_class, adeq_dbg = _fetch_adequabilidade_unifamiliar(zone_sigla=zone_sigla, via_tipo_texto=via_tipo)
    via_norm = _via_tipo_norm(via_tipo)
    icon, status_curto, explicacao = _summarize_adequabilidade(zone_class=zone_class, via_norm=via_norm, via_class=via_class)

    return {
        "rule": rule,
        "area": area,
        "front": front,
        "depth": depth,
        "built_ground": built_ground,
        "permeable_area": permeable_area,
        "is_corner": is_corner,
        "is_irregular": is_irregular,
        "tipo_lote": tipo_lote,
        "zone": zone,
        "via": via,
        "via_tipo": via_tipo,
        "uso": uso,
        "subzona": subzona,
        "to_max": to_max,
        "tp_min": tp_min,
        "ia_max": ia_max,
        "ia_min": _pick_number(rule.get("ia_min"), calc.get("ia_min")),
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
        "zone_description": zone_desc,
        "zone_sigla": zone_sigla,
        "subzone_code": subzone_code,
        "zone_label": zone_label,
        "zone_title": _pick_text((zone_desc or {}).get("title"), default=zone_sigla or zone),
        "zone_class": zone_class,
        "via_class": via_class,
        "adeq_dbg": adeq_dbg,
        "via_norm": via_norm,
        "icon": icon,
        "status_curto": status_curto,
        "explicacao": explicacao,
        "pav_est": max(1, int(gabarito // 3.0)) if gabarito is not None and gabarito > 0 else None,
    }





def _norm(s: Any) -> str:
    return str(s or "").strip().upper()


def _sigla_nome(sigla: str) -> str:
    s = _norm(sigla)
    mapa = {
        "A": "Adequado",
        "I": "Inadequado",
        "AP": "Adequado (pequeno porte)",
        "AM": "Adequado (medio porte)",
        "AP/AM": "Depende do porte (pequeno/medio)",
        "PE": "Projeto especial",
    }
    return mapa.get(s, "")


def _zone_candidates(z: str) -> List[str]:
    z0 = _norm(z)
    cands = [z0]
    if " " in z0:
        cands.append(z0.replace(" ", ""))
    else:
        import re
        z_sp = re.sub(r"(\D)(\d)", r"\1 \2", z0)
        if z_sp != z0:
            cands.append(z_sp)
    cands.append(z0.replace("-", " "))
    out: List[str] = []
    for c in cands:
        c = c.strip().upper()
        if c and c not in out:
            out.append(c)
    return out


def _via_tipo_norm(v: Any) -> Optional[str]:
    s = str(v or "").strip().lower()
    if not s:
        return None
    if "arterial" in s and "pais" in s:
        return "ARTERIAL_PAISAGISTICA"
    if "coletora" in s and "pais" in s:
        return "COLETORA_PAISAGISTICA"
    if "arterial" in s:
        return "ARTERIAL"
    if "coletora" in s:
        return "COLETORA"
    return None


def _get_supabase():
    try:
        from core.supabase_client import get_supabase  # type: ignore
        return get_supabase()
    except Exception:
        return None


def _fetch_adequabilidade(*, zone_sigla: str, via_tipo_texto: Optional[str], use_type_code: str) -> tuple[Optional[str], Optional[str], Dict[str, Any]]:
    sb = _get_supabase()
    debug: Dict[str, Any] = {
        "zone_sigla_in": zone_sigla,
        "zone_candidates": [],
        "use_type_code": use_type_code,
        "via_tipo_in": via_tipo_texto,
        "via_tipo_norm": None,
    }
    if sb is None:
        debug["error"] = "supabase_client_not_available"
        return None, None, debug

    zona = _norm(zone_sigla)
    use_code = _norm(use_type_code)
    via_norm = _via_tipo_norm(via_tipo_texto)
    debug["via_tipo_norm"] = via_norm

    zone_class = None
    via_class = None
    try:
        cands = _zone_candidates(zona)
        debug["zone_candidates"] = cands
        res = (
            sb.table("adequab_zonas_sede")
            .select("zone_sigla,classificacao")
            .eq("use_type_code", use_code)
            .in_("zone_sigla", cands)
            .limit(1)
            .execute()
        )
        data = getattr(res, "data", None) or []
        if data:
            zone_class = (data[0].get("classificacao") or "").strip()
            debug["zone_hit"] = data[0].get("zone_sigla")
    except Exception as e:
        debug["zone_error"] = str(e)

    if via_norm:
        try:
            res2 = (
                sb.table("adequab_vias")
                .select("classificacao")
                .eq("use_type_code", use_code)
                .eq("via_tipo", via_norm)
                .limit(1)
                .execute()
            )
            data2 = getattr(res2, "data", None) or []
            if data2:
                via_class = (data2[0].get("classificacao") or "").strip()
        except Exception as e:
            debug["via_error"] = str(e)

    return zone_class, via_class, debug


def _fetch_adequabilidade_unifamiliar(zone_sigla: str, via_tipo_texto: str | None) -> tuple[str | None, str | None, dict[str, Any]]:
    attempts: list[tuple[str, str | None, str | None, dict[str, Any]]] = []
    for use_code in ("RES_UNI", "RES_MULTI_R21", "RES_MULTI_R22", "RES_MULTI_R3"):
        zc, vc, dbg = _fetch_adequabilidade(
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


def _summarize_adequabilidade(*, zone_class: str | None, via_norm: str | None, via_class: str | None) -> tuple[str, str, str]:
    z = _norm(zone_class)
    v = _norm(via_class)

    if not via_norm:
        if z == "I":
            return ("❌", "NÃO PERMITE", "A zona indicou I (Inadequado / nao permitido). Em via local, normalmente vale a regra da zona.")
        if z == "AP/AM":
            return ("⚠️", "DEPENDE DO PORTE", "A zona indicou AP/AM (depende do porte). Em via local, normalmente vale a regra da zona.")
        if z == "PE":
            return ("⚠️", "PROJETO ESPECIAL", "A zona indicou PE (Projeto especial). Pode exigir analise/condicoes extras no licenciamento.")
        if z in ("A", "AP", "AM"):
            return ("✅", "PERMITE", "A zona permite. Ainda e obrigatorio cumprir TO, TP, IA, recuos, altura e as demais regras aplicaveis.")
        return ("⚠️", "SEM DADO", "Nao foi possivel determinar o resultado por zona.")

    if v == "I":
        return ("❌", "NÃO PERMITE", "O tipo de via indicou I (nao permitido), mesmo que a zona permita.")
    if z == "I" and v in ("A", "AP", "AM"):
        return ("⚠️", "POSSÍVEL PELA VIA", "A zona deu I, mas o tipo de via permite. O licenciamento pode considerar o resultado por tipo de via.")
    if z == "I" and v == "AP/AM":
        return ("⚠️", "DEPENDE DO PORTE", "A zona deu I, mas o tipo de via deu AP/AM (depende do porte). Pode depender do licenciamento.")
    if z == "I" and v == "PE":
        return ("⚠️", "PROJETO ESPECIAL", "A zona deu I, mas o tipo de via indica PE (Projeto especial). Pode exigir analise/condicoes extras.")
    if z == "AP/AM" or v == "AP/AM":
        return ("⚠️", "DEPENDE DO PORTE", "Existe indicacao AP/AM (depende do porte). Confira se o empreendimento e pequeno ou medio.")
    if z == "PE" or v == "PE":
        return ("⚠️", "PROJETO ESPECIAL", "Existe indicacao PE (Projeto especial). Pode exigir analise/condicoes extras no licenciamento.")
    return ("✅", "PERMITE", "Zona e/ou tipo de via permitem. Ainda e obrigatorio cumprir TO, TP, IA, recuos, altura e as demais regras aplicaveis.")
def _fetch_zone_description(zone_sigla: str, subzone_code: str, zone_label: str = "") -> Optional[Dict[str, Any]]:
    try:
        return fetch_zone_description(zone_sigla or "", subzone_code or "PADRAO", zone_label or zone_sigla or "")
    except Exception:
        return None


def _render_zone_description_block(pdf: _ReportPDF, ctx: Dict[str, Any]) -> None:
    desc = ctx.get("zone_description") or {}
    text = _pick_text(desc.get("description_text"))
    if not text:
        return
    title = _pick_text(desc.get("title"), default="Descricao da zona")
    _section_title(pdf, "DESCRICAO DA ZONA")
    pdf.set_font("Helvetica", "B", 10.8)
    pdf.multi_cell(_full_width(pdf), 5.4, _sanitize(title))
    pdf.ln(0.6)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(_full_width(pdf), 5.3, _sanitize(text))

def _meta_header(pdf: _ReportPDF, ctx: Dict[str, Any], generated_at: str) -> None:
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(110, 110, 110)
    pdf.cell(0, 5, _sanitize(f"Emitido em: {generated_at}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(1)

    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(225, 229, 235)
    y = pdf.get_y()
    pdf.rounded_rect(pdf.l_margin, y, _full_width(pdf), 22, 2.0, style="DF")
    pdf.set_xy(pdf.l_margin + 3, y + 2.3)
    pdf.set_font("Helvetica", "B", 12)
    label_uso = "Residencial Unifamiliar" if str(ctx["uso"]).startswith("RES_UNI") else str(ctx["uso"])
    pdf.cell(0, 5, _sanitize(label_uso))
    pdf.set_xy(pdf.l_margin + 3, y + 8)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(_full_width(pdf) - 6, 5.3, _sanitize(
        f"Terreno: {_fmt_area(ctx['area'])}   Dimensoes: {_fmt_m(ctx['front'])} x {_fmt_m(ctx['depth'])}   Zona: {ctx['zone']}   Tipo: {ctx['tipo_lote']}"
    ))
    pdf.set_x(pdf.l_margin + 3)
    pdf.set_text_color(95, 95, 95)
    pdf.multi_cell(_full_width(pdf) - 6, 5.1, _sanitize(
        f"Via: {ctx['via']} | Tipo de via: {ctx['via_tipo']} | Uso: {ctx['uso']} | Subzona: {ctx['subzona']}"
    ))
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(y + 25)


def _render_localizacao_indices_analise(pdf: _ReportPDF, ctx: Dict[str, Any]) -> None:
    rule = ctx["rule"]
    area = ctx["area"]
    built_ground = ctx["a_adotada"] or ctx["built_ground"]
    ia_utilizado = (built_ground / area) if (built_ground is not None and area not in (None, 0)) else None
    to_utilizada = ((built_ground / area) * 100.0) if (built_ground is not None and area not in (None, 0)) else None
    permeavel_prev = ctx["permeable_area"]
    tp_prevista = ((permeavel_prev / area) * 100.0) if (permeavel_prev is not None and area not in (None, 0)) else ctx["tp_min"]

    _section_title(pdf, "3) LOCALIZACAO (ZONA + VIA)", small=True)
    _key_value_row(pdf,
        [("Uso", ctx["uso"]), ("Zona", ctx["zone"]), ("Rua / Logradouro", ctx["via"])],
        [32, 32, _full_width(pdf) - 64 - 5.0]
    )
    _key_value_row(pdf,
        [("Tipo de via", ctx["via_tipo"]), ("Subzona", ctx["subzona"]), ("Tipo de lote", ctx["tipo_lote"])],
        [54, 52, _full_width(pdf) - 106 - 5.0]
    )

    _section_title(pdf, "4) INDICES URBANISTICOS (SUPABASE)", small=True)
    _key_value_row(pdf,
        [("Taxa de Permeabilidade (TP) minima", _fmt_pct(ctx["tp_min"])), ("Taxa de Ocupacao (TO) maxima", _fmt_pct(ctx["to_max"])), ("TO do Subsolo maxima", _fmt_pct(rule.get("to_subsolo_max_pct") or rule.get("to_subsolo_max")) )],
        [60, 60, _full_width(pdf) - 120 - 5.0]
    )
    _key_value_row(pdf,
        [("Indice de Aproveitamento (IA) maximo", _fmt_int_or_num(ctx["ia_max"])), ("Recuo de Frente", _fmt_m(ctx["rec_fr"])), ("Recuo de Fundo", _fmt_m(ctx["rec_fun"])), ("Recuo Lateral", _fmt_m(ctx["rec_lat"]))],
        [48, 38, 38, _full_width(pdf) - 124 - 7.5]
    )
    testada_min = _pick_text(rule.get("testada_min_m"), rule.get("testada_min"), default="-")
    testada_max = _pick_text(rule.get("testada_max_m"), rule.get("testada_max"), default="-")
    area_min = _fmt_area(rule.get("lote_min_m2") or rule.get("area_lote_min_m2") or rule.get("area_min_lote_m2"))
    area_max = _fmt_area(rule.get("lote_max_m2") or rule.get("area_lote_max_m2") or rule.get("area_max_lote_m2"))
    _key_value_row(pdf,
        [("Area minima do lote", area_min), ("Area maxima do lote", area_max), ("Testada minima", _pick_text(testada_min)), ("Testada maxima", _pick_text(testada_max)), ("Altura maxima", _fmt_m(ctx["gabarito"]))],
        [36, 36, 34, 34, _full_width(pdf) - 140 - 10.0]
    )

    _section_title(pdf, "5) ANALISE URBANISTICA", small=True)
    if ia_utilizado is not None:
        _paragraph(pdf, f"IA utilizado (considerando terreo adotado): {ia_utilizado:.2f}")
    if to_utilizada is not None:
        _paragraph(pdf, f"TO utilizada: {_fmt_pct(to_utilizada)}")
    if tp_prevista is not None:
        _paragraph(pdf, f"TP prevista: {_fmt_pct(tp_prevista)}")

    if to_utilizada is not None and ctx["to_max"] is not None:
        _status_box(pdf, "Taxa de Ocupacao dentro do permitido", to_utilizada <= ctx["to_max"] + 1e-9)
    if ia_utilizado is not None and ctx["ia_max"] is not None:
        _status_box(pdf, "Indice de Aproveitamento dentro do permitido", ia_utilizado <= ctx["ia_max"] + 1e-9)
    if tp_prevista is not None and ctx["tp_min"] is not None:
        _status_box(pdf, "Taxa de Permeabilidade atende o minimo", tp_prevista + 1e-9 >= ctx["tp_min"])


def _render_relatorio_narrativo(pdf: _ReportPDF, ctx: Dict[str, Any]) -> None:
    area = ctx["area"]
    front = ctx["front"]
    depth = ctx["depth"]
    is_irregular = ctx["is_irregular"]
    built_ground = ctx["built_ground"]
    a_adotada = ctx["a_adotada"]
    a_to = ctx["a_to"]
    tp_min = ctx["tp_min"]
    a_perm_min = ctx["a_perm_min"]
    ia_max = ctx["ia_max"]
    a_total = ctx["a_total"]
    rec_fr = ctx["rec_fr"]
    rec_lat = ctx["rec_lat"]
    rec_fun = ctx["rec_fun"]
    w_util = ctx["w_util"]
    d_util = ctx["d_util"]
    a_recuos = ctx["a_recuos"]
    a_op1_max = ctx["a_op1_max"]
    a_op2_max = ctx["a_op2_max"]

    def tp_scenario(a_terreo: float | None) -> Optional[tuple[float, float]]:
        if a_terreo is None or a_perm_min is None or area is None:
            return None
        a_rest = area - a_terreo
        a_imperm = a_rest - a_perm_min
        return a_rest, a_imperm

    _section_title(pdf, "6) RELATORIO URBANISTICO", small=True)
    pdf.set_fill_color(255, 255, 255)
    pdf.set_draw_color(220, 224, 230)
    y = pdf.get_y()
    pdf.rounded_rect(pdf.l_margin, y, _full_width(pdf), 16, 2.0, style="D")
    pdf.set_xy(pdf.l_margin + 3, y + 2.5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(24, 41, 74)
    pdf.cell(0, 5, _sanitize("RELATORIO URBANISTICO"))
    pdf.set_xy(pdf.l_margin + 3, y + 8.5)
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(_full_width(pdf) - 6, 4.8, _sanitize(
        f"Terreno: {_fmt_area(area)} | Dimensoes: {_fmt_m(front)} x {_fmt_m(depth)} | Zona: {ctx['zone']} | Tipo: {ctx['tipo_lote']}"
    ))
    pdf.set_y(y + 19)

    _section_title(pdf, "1. Quanto posso ocupar no chao?", small=True)
    if ctx["to_max"] is None or a_to is None:
        _paragraph(pdf, "Sem TO maxima cadastrada para esta zona/uso.")
    else:
        _paragraph(pdf, f"A zona permite ocupar ate {_fmt_pct(ctx['to_max'])} do terreno no terreo.")
        _paragraph(pdf, f"{_fmt_area(area)} x {_fmt_pct(ctx['to_max'])} = {_fmt_area(a_to)}", bold=True)
        _paragraph(pdf, "Esse e o limite maximo permitido pela Taxa de Ocupacao (TO).")
        if a_adotada is not None:
            if built_ground is not None and a_adotada < built_ground:
                _paragraph(pdf, f"Voce informou {_fmt_area(built_ground)} no terreo, mas o maximo permitido e {_fmt_area(a_adotada)}. Os calculos abaixo usam o valor permitido.", color=(175, 103, 22))
            else:
                _paragraph(pdf, f"Area considerada no seu projeto (terreo): {_fmt_area(a_adotada)}.", color=(26, 112, 62))
        _paragraph(pdf, "Agora veja duas situacoes possiveis:")
        if not is_irregular:
            _paragraph(pdf, "Opcao 1 - Respeitando os recuos padrao", bold=True)
            _bullet_list(pdf, [
                f"Frontal: {_fmt_m(rec_fr)}",
                f"Laterais: {_fmt_m(rec_lat)} cada",
                f"Fundo: {_fmt_m(rec_fun)}",
            ])
            _paragraph(pdf, f"Largura util: {_fmt_m(front)} - {_fmt_m(rec_lat)} - {_fmt_m(rec_lat)} = {_fmt_m(w_util)}")
            _paragraph(pdf, f"Profundidade util: {_fmt_m(depth)} - {_fmt_m(rec_fr)} - {_fmt_m(rec_fun)} = {_fmt_m(d_util)}")
            if a_recuos is not None:
                _paragraph(pdf, f"{_fmt_m(w_util)} x {_fmt_m(d_util)} = {_fmt_area(a_recuos)}", bold=True)
            if a_op1_max is not None:
                _paragraph(pdf, f"Nesse caso, mesmo podendo ocupar {_fmt_area(a_to)} pela regra da zona, o limite fisico pelos recuos e {_fmt_area(a_op1_max)}.")
        else:
            _paragraph(pdf, "Terreno irregular: como o lote nao e retangular, o relatorio nao calcula a implantacao por recuos. Aqui sao apresentados apenas os limites legais por TO, TP e IA.")
        _paragraph(pdf, "Opcao 2 - Implantacao no alinhamento (Art. 112 - LC 90/2023)", bold=True)
        _paragraph(pdf, "Por se tratar de residencia unifamiliar, a legislacao permite zerar o recuo frontal e os recuos laterais, desde que:")
        _bullet_list(pdf, [
            "Seja respeitada a Taxa de Ocupacao (TO) maxima",
            "Seja respeitada a Taxa de Permeabilidade (TP) minima",
        ])
        _paragraph(pdf, "Nesse caso, voce pode utilizar no terreo ate o limite permitido pela TO.")
        _paragraph(pdf, "O recuo de fundo permanece obrigatorio.")
        if a_op2_max is not None:
            _paragraph(pdf, f"Terreo maximo nesta opcao: {_fmt_area(a_op2_max)}", bold=True)

    _section_title(pdf, "2. Quanto preciso deixar livre?", small=True)
    if tp_min is None or a_perm_min is None:
        _paragraph(pdf, "Sem TP minima cadastrada para esta zona/uso.")
    else:
        _paragraph(pdf, f"A zona exige {_fmt_pct(tp_min)} de area permeavel.")
        _paragraph(pdf, f"{_fmt_area(area)} x {_fmt_pct(tp_min)} = {_fmt_area(a_perm_min)} obrigatorios permeaveis", bold=True)
        if a_adotada is not None:
            tp_user = tp_scenario(a_adotada)
            if tp_user:
                a_rest, a_imperm = tp_user
                _paragraph(pdf, "Cenario com a area adotada para o seu projeto", bold=True)
                _paragraph(pdf, f"Se voce utilizar {_fmt_area(a_adotada)} no terreo, a area restante no lote sera {_fmt_area(a_rest)}.")
                _bullet_list(pdf, [
                    f"{_fmt_area(a_perm_min)} devem permitir infiltracao no solo",
                    f"{_fmt_area(a_imperm)} podem receber piso impermeavel",
                ])
        tp2 = tp_scenario(a_op2_max)
        if tp2:
            a_rest, a_imperm = tp2
            _paragraph(pdf, "Cenario pela Opcao 2 (Art. 112)", bold=True)
            _paragraph(pdf, f"Usando {_fmt_area(a_op2_max)} no terreo, sobra {_fmt_area(a_rest)} no lote.")
            _bullet_list(pdf, [
                f"{_fmt_area(a_perm_min)} devem permitir infiltracao no solo",
                f"{_fmt_area(a_imperm)} podem receber piso impermeavel",
            ])
        headers = ["Tipo de Piso", "Percentual considerado permeavel"]
        rows = [[a, b] for a, b in PERMEABILIDADE_ROWS]
        _simple_table(pdf, headers, rows, [110, 70], font_size=9)
        pdf.ln(2)
        _paragraph(pdf, "Isso significa que nem todo piso externo conta 100% como permeavel.")

    _section_title(pdf, "3. Posso construir mais andares?", small=True)
    if ia_max is None or a_total is None:
        _paragraph(pdf, "Sem IA maximo cadastrado para esta zona/uso.")
    else:
        _paragraph(pdf, "Alem do limite no chao, existe o limite total permitido.")
        _paragraph(pdf, f"Indice de Aproveitamento (IA): {_fmt_num(ia_max)}", bold=True)
        _paragraph(pdf, f"{_fmt_area(area)} x {_fmt_num(ia_max)} = {_fmt_area(a_total)} no total", bold=True)
        _paragraph(pdf, f"Isso significa que voce pode distribuir ate {_fmt_area(a_total)} somando todos os pavimentos.")
    if ctx["gabarito"] is not None:
        _paragraph(pdf, f"Altura maxima da zona: {_fmt_m(ctx['gabarito'])}", bold=True)

    _section_title(pdf, "4. Estacionamento", small=True)
    _paragraph(pdf, "De acordo com o Anexo IV da Lei Complementar nº 90/2023, nao ha previsao de quantidade minima obrigatoria de vagas para residencia unifamiliar.")
    _paragraph(pdf, "A exigencia de vagas aplica-se as residencias multifamiliares e demais atividades listadas no Anexo IV.")


def _render_quadro_tecnico(pdf: _ReportPDF) -> None:
    _section_title(pdf, "QUADRO TECNICO - PARAMETROS DOS AMBIENTES")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 90, 90)
    pdf.multi_cell(_full_width(pdf), 5.3, _sanitize("Lei Complementar nº 90/2023 - Anexo II"))
    pdf.set_text_color(0, 0, 0)
    headers = ["AMBIENTE", "CIRCULO INSCRITO", "AREA MINIMA", "ILUMINACAO", "VENTILACAO", "PE-DIREITO", "OBS."]
    rows = [[row[h] for h in headers] for row in QUADRO_ROWS]
    _simple_table(pdf, headers, rows, [44, 28, 26, 23, 23, 24, 18], font_size=8.6, line_h=5.0)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.multi_cell(_full_width(pdf), 5.5, _sanitize("Observacoes aplicaveis (Anexo II - LC 90/2023)"))
    pdf.set_font("Helvetica", "", 10)
    _bullet_list(pdf, QUADRO_OBS)


def _render_dicas_valiosas(pdf: _ReportPDF, is_corner: bool = False) -> None:
    _section_title(pdf, "DICAS VALIOSAS")
    for item in get_dicas_valiosas(is_corner=is_corner):
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            titulo = str(item[0] or "").strip()
            texto = str(item[1] or "").strip()
            if titulo:
                pdf.set_font("Helvetica", "B", 10.8)
                pdf.multi_cell(_full_width(pdf), 5.4, _sanitize(titulo + ":"))
            if texto:
                pdf.set_font("Helvetica", "", 10)
                pdf.multi_cell(_full_width(pdf), 5.3, _sanitize(texto))
                pdf.ln(1)
            continue
        texto = str(item or "").strip()
        if not texto:
            continue
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(_full_width(pdf), 5.3, _sanitize(texto))
        pdf.ln(1)


def _render_figuras(pdf: _ReportPDF, figures: List[Dict[str, Any]]) -> None:
    if not figures:
        return
    _section_title(pdf, "FIGURAS ANEXAS (ANEXO V)")
    temp_files: List[str] = []
    try:
        for index, figure in enumerate(figures, start=1):
            title = _pick_text(figure.get("title"), default=f"Figura {index}")
            caption = _pick_text(figure.get("caption"), default="")
            url = figure.get("url")
            # cada figura em nova pagina para evitar quebra feia entre titulo/imagem/rodape
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(24, 41, 74)
            pdf.multi_cell(_full_width(pdf), 6.5, _sanitize(title))
            pdf.set_text_color(0, 0, 0)
            if caption and caption != title:
                pdf.set_font("Helvetica", "", 9.5)
                pdf.set_text_color(95, 95, 95)
                pdf.multi_cell(_full_width(pdf), 5.0, _sanitize(caption))
                pdf.set_text_color(0, 0, 0)
                pdf.ln(1)
            if not url:
                _paragraph(pdf, "Figura sem URL publica disponivel.")
                continue
            temp = _download_temp_image(url)
            if not temp:
                _paragraph(pdf, "Nao foi possivel carregar esta figura no PDF.")
                continue
            temp_files.append(temp)
            max_w = _full_width(pdf)
            max_h = pdf.h - pdf.get_y() - pdf.b_margin - 8
            img_w, img_h = _fit_image_size(temp, max_w, max_h)
            if img_h > max_h and max_h > 20:
                img_w, img_h = _fit_image_size(temp, max_w, max_h)
            try:
                x = pdf.l_margin + ((_full_width(pdf) - img_w) / 2)
                pdf.image(temp, x=x, y=pdf.get_y(), w=img_w, h=img_h)
                pdf.set_y(pdf.get_y() + img_h + 3)
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(110, 110, 110)
                pdf.multi_cell(_full_width(pdf), 4.5, _sanitize("Anexo V - LC 90/2023"), align="C")
                pdf.set_text_color(0, 0, 0)
            except Exception:
                _paragraph(pdf, "Nao foi possivel renderizar esta figura no PDF.")
    finally:
        for path in temp_files:
            try:
                os.remove(path)
            except Exception:
                pass



def _html(v: Any) -> str:
    return _html_escape(str(v if v is not None else ""), quote=True)


def _status_kind(status_curto: str) -> str:
    s = _norm(status_curto)
    if s == "PERMITE":
        return "success"
    if s in {"DEPENDE DO PORTE", "PROJETO ESPECIAL", "POSSÍVEL PELA VIA", "SEM DADO"}:
        return "warning"
    return "danger"


def _summary_box(title: str, value: str, tone: str = "default") -> str:
    return f'<div class="summary-card {tone}"><div class="summary-label">{_html(title)}</div><div class="summary-value">{_html(value)}</div></div>'


def _kv_item(label: str, value: str) -> str:
    return f'<div class="kv-item"><div class="kv-label">{_html(label)}</div><div class="kv-value">{_html(value)}</div></div>'


def _bullet_items(items: Sequence[str]) -> str:
    lis = ''.join(f'<li>{_html(item)}</li>' for item in items if str(item or '').strip())
    return f'<ul class="bullet-list">{lis}</ul>' if lis else ''


def _table_html(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    thead = ''.join(f'<th>{_html(h)}</th>' for h in headers)
    body_rows = []
    for row in rows:
        body_rows.append('<tr>' + ''.join(f'<td>{_html(cell)}</td>' for cell in row) + '</tr>')
    return '<div class="table-wrap"><table><thead><tr>' + thead + '</tr></thead><tbody>' + ''.join(body_rows) + '</tbody></table></div>'


def _formula_box_html(text: str) -> str:
    return f'<div class="formula-box">👉 {_html(text)}</div>'


def _info_box_html(title: str, content: str, tone: str = "default") -> str:
    return f'<div class="info-box {tone}"><div class="info-title">{_html(title)}</div><div class="info-content">{content}</div></div>'


def _section_card(title: str, body_html: str, number: int, accent: str = "") -> str:
    accent_html = f'<span class="section-accent">{_html(accent)}</span>' if accent else ''
    return (
        '<section class="section-card">'
        f'<div class="section-head"><div class="section-badge">{number:02d}</div>'
        f'<div class="section-title-wrap"><h2>{accent_html}{_html(title)}</h2></div></div>'
        f'<div class="section-body">{body_html}</div></section>'
    )


def _render_unifamiliar_report_html(ctx: Dict[str, Any], payload: Dict[str, Any]) -> str:
    area = ctx.get("area")
    a_to = ctx.get("a_to")
    a_perm_min = ctx.get("a_perm_min")
    a_total = ctx.get("a_total")
    a_recuos = ctx.get("a_recuos")
    a_op2_max = ctx.get("a_op2_max")
    status_curto = str(ctx.get("status_curto") or "")
    status_kind = _status_kind(status_curto)
    zone_desc = ctx.get("zone_description") or {}
    zone_desc_title = _pick_text(zone_desc.get("title"), default=ctx.get("zone_title") or ctx.get("zone") or "-")
    zone_desc_text = _pick_text(zone_desc.get("description_text"), default="Descrição da zona não encontrada.")
    ia_min_texto = _fmt_num(ctx.get("ia_min")) if ctx.get("ia_min") is not None else "não informado"
    figures = payload.get("figures", []) or []
    generated_at = payload.get("generated_at") or "-"

    def tp_scenario(a_terreo: float | None):
        if a_terreo is None or a_perm_min is None or area in (None, 0):
            return None
        a_rest = area - a_terreo
        a_imperm = a_rest - a_perm_min
        return a_rest, a_imperm

    def _callout(content: str, tone: str = "default") -> str:
        return f'<div class="callout {tone}">{content}</div>'

    def _markdown_list(items: Sequence[str]) -> str:
        return '<ul class="plain-list">' + ''.join(f'<li>{_html(i)}</li>' for i in items if str(i or '').strip()) + '</ul>'

    body: List[str] = []
    body.append(f"""
<html>
<head>
<meta charset="utf-8">
<style>
@page {{
  size: A4;
  margin: 16mm 14mm 16mm 14mm;
  @bottom-center {{ content: "Página " counter(page); color: #6b7280; font-size: 9px; }}
}}
:root {{
  --bg:#ffffff;
  --ink:#111827;
  --muted:#6b7280;
  --line:#e5e7eb;
  --panel:#f8fafc;
  --panel2:#f3f4f6;
  --accent:#f97316;
  --accent-soft:#fff7ed;
  --success:#166534;
  --success-bg:#ecfdf5;
  --success-line:#bbf7d0;
  --warning:#92400e;
  --warning-bg:#fffbeb;
  --warning-line:#fde68a;
  --danger:#991b1b;
  --danger-bg:#fef2f2;
  --danger-line:#fecaca;
  --brand:#1f3b69;
}}
* {{ box-sizing:border-box; }}
body {{ font-family: DejaVu Sans, Arial, sans-serif; font-size:10.5pt; line-height:1.58; color:var(--ink); background:var(--bg); }}
p, h1, h2, h3, h4 {{ margin:0; }}
.report-title {{ font-size:23px; font-weight:800; color:var(--brand); margin-bottom:8px; }}
.lead {{ color:#374151; margin-top:10px; }}
.meta-top {{ margin-top:8px; color:var(--muted); font-size:9.2pt; }}
.intro-box {{ margin-top:14px; background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:16px 18px; }}
.intro-box strong {{ color:#0f172a; }}
.hero-grid {{ display:grid; grid-template-columns:repeat(2,1fr); gap:10px; margin-top:14px; }}
.hero-card {{ background:#fff; border:1px solid var(--line); border-radius:12px; padding:11px 12px; }}
.hero-label {{ color:var(--muted); font-size:8.8pt; text-transform:uppercase; letter-spacing:.04em; margin-bottom:5px; }}
.hero-value {{ font-size:10.8pt; font-weight:700; color:#0f172a; line-height:1.35; }}
hr.sep {{ border:none; border-top:1px solid var(--line); margin:22px 0 16px; }}
.section-title {{ font-size:16px; font-weight:800; color:#0f172a; margin-bottom:10px; }}
.section-body > * + * {{ margin-top:10px; }}
.callout {{ border:1px solid var(--line); background:var(--panel); border-radius:12px; padding:12px 13px; }}
.callout.success {{ color:var(--success); background:var(--success-bg); border-color:var(--success-line); }}
.callout.warning {{ color:var(--warning); background:var(--warning-bg); border-color:var(--warning-line); }}
.callout.danger {{ color:var(--danger); background:var(--danger-bg); border-color:var(--danger-line); }}
.kv-grid {{ display:grid; grid-template-columns:repeat(2,1fr); gap:10px; margin-top:8px; }}
.kv-item {{ background:#fff; border:1px solid var(--line); border-radius:12px; padding:10px 11px; }}
.kv-label {{ color:var(--muted); font-size:8.7pt; text-transform:uppercase; letter-spacing:.05em; margin-bottom:4px; }}
.kv-value {{ color:#0f172a; font-size:10.7pt; font-weight:700; line-height:1.38; }}
.rule-grid {{ display:grid; grid-template-columns:repeat(2,1fr); gap:10px; margin-top:10px; }}
.rule-card {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:11px 12px; }}
.rule-label {{ color:var(--muted); font-size:8.7pt; text-transform:uppercase; letter-spacing:.05em; margin-bottom:4px; }}
.rule-value {{ font-size:12pt; font-weight:800; color:#0f172a; }}
.formula-box {{ background:var(--accent-soft); border:1px solid #fed7aa; border-radius:12px; padding:10px 12px; font-weight:700; color:#9a3412; }}
.plain-list {{ margin:0; padding-left:18px; }}
.plain-list li + li {{ margin-top:4px; }}
.table-wrap {{ margin-top:10px; overflow:hidden; border:1px solid var(--line); border-radius:14px; }}
table {{ width:100%; border-collapse:collapse; font-size:9.3pt; }}
thead th {{ background:#f8fafc; color:#334155; text-align:left; padding:10px 9px; font-weight:800; border-bottom:1px solid var(--line); }}
tbody td {{ padding:9px; border-bottom:1px solid var(--line); vertical-align:top; }}
tbody tr:last-child td {{ border-bottom:none; }}
.two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
.subheading {{ font-weight:800; color:#111827; margin-top:2px; }}
.checklist li::marker {{ content:"☐ "; }}
.figure-card {{ border:1px solid var(--line); border-radius:14px; overflow:hidden; background:#fff; margin-top:10px; }}
.figure-card img {{ width:100%; display:block; }}
.figure-meta {{ padding:10px 12px; }}
.figure-title {{ font-weight:700; color:#111827; }}
.footer-note {{ margin-top:18px; color:var(--muted); font-size:9pt; border-top:1px solid var(--line); padding-top:10px; }}
.muted {{ color:var(--muted); }}
.page-break-before {{ page-break-before:always; }}
.no-break {{ page-break-inside:avoid; break-inside:avoid; }}
</style>
</head>
<body>
""")

    body.append('<div class="report-title">🏡 RELATÓRIO URBANÍSTICO</div>')
    body.append('<div class="meta-top">Viabilidade Fácil / Viabilidade Urbana Sobral • Emitido em ' + _html(generated_at) + '</div>')
    body.append(
        '<div class="intro-box">'
        '<p>Este relatório mostra, de forma simples, o que pode ou não pode ser feito no terreno informado, com base na zona, na via e nas regras urbanísticas do município.</p>'
        '<p class="lead">A ideia aqui é facilitar a leitura: primeiro mostramos onde o terreno está, depois se o uso é viável, e em seguida explicamos os principais limites do lote, como ocupação, área livre, altura, vagas, ambientes mínimos e calçada.</p>'
        '<p class="lead"><strong>Importante:</strong> este relatório é uma análise inicial. A aprovação final depende da conferência completa no licenciamento.</p>'
        '</div>'
    )
    body.append(
        '<div class="hero-grid">'
        + _kv_item('Uso analisado', 'Residência unifamiliar')
        + _kv_item('Zona', str(ctx.get('zone') or '-'))
        + _kv_item('Via', str(ctx.get('via') or '-'))
        + _kv_item('Resultado', status_curto or '-')
        + '</div>'
    )

    # 01
    body.append('<hr class="sep"><div class="section-title">📍 1️⃣ Onde está localizado o terreno?</div><div class="section-body">')
    body.append('<p>Aqui estão os dados principais usados nesta análise:</p>')
    body.append('<div class="kv-grid">' + ''.join([
        _kv_item('Uso informado', 'Residência unifamiliar'),
        _kv_item('Área do terreno', _fmt_area(area)),
        _kv_item('Dimensões', f'{_fmt_m(ctx.get("front"))} × {_fmt_m(ctx.get("depth"))}'),
        _kv_item('Zona', str(ctx.get('zone') or '-')),
        _kv_item('Subzona / setor', str(ctx.get('subzone_code') or ctx.get('subzona') or '-')),
        _kv_item('Tipo de lote', str(ctx.get('tipo_lote') or '-')),
        _kv_item('Via', str(ctx.get('via') or '-')),
        _kv_item('Tipo de via', str(ctx.get('via_tipo') or '-')),
    ]) + '</div>')
    body.append('<p class="muted">Essas informações são a base de todo o relatório.</p></div>')

    # 02
    body.append('<hr class="sep"><div class="section-title">✅ 2️⃣ O uso residencial unifamiliar é viável neste terreno?</div><div class="section-body">')
    body.append('<p><strong>Para o uso residencial unifamiliar, a permissão pode depender principalmente da zona e, em alguns casos, também do tipo da via.</strong></p>')
    via_line = (
        f"Por via: {ctx.get('via_class')} ({_sigla_nome(ctx.get('via_class'))})"
        if ctx.get('via_norm') and ctx.get('via_class')
        else f"Por via: {ctx.get('via_tipo') or 'via local'}"
    )
    body.append(_callout(
        '<div><strong>Por zona:</strong> ' + _html((ctx.get('zone_class') or 'não encontrado') + ((f" ({_sigla_nome(ctx.get('zone_class'))})") if ctx.get('zone_class') else '')) + '</div>'
        '<div style="margin-top:6px"><strong>' + _html(via_line.split(':')[0]) + ':</strong> ' + _html(via_line.split(':',1)[1].strip()) + '</div>'
        '<div style="margin-top:6px"><strong>Resumo final:</strong> ' + _html((ctx.get('icon') or '') + ' ' + (status_curto or '-')) + '</div>'
    ))
    body.append(_callout('<strong>' + _html((ctx.get('icon') or '') + ' Resumo final: ' + (status_curto or '-')) + '.</strong> ' + _html(str(ctx.get('explicacao') or '')), status_kind))
    body.append('<p><strong>Mesmo quando o resultado for positivo, ainda é necessário cumprir TO, TP, IA, recuos, altura e as demais regras aplicáveis.</strong></p></div>')

    # 03
    body.append('<hr class="sep"><div class="section-title">📘 3️⃣ Como funciona a leitura da adequabilidade no unifamiliar?</div><div class="section-body">')
    body.append('<p><strong>No unifamiliar, o resultado não depende só do nome da zona. Em alguns casos, também é preciso observar o tipo da via. Por isso, estas siglas ajudam a interpretar corretamente a viabilidade mostrada acima.</strong></p>')
    body.append('<div class="two-col">')
    body.append(_table_html(['Sigla', 'O que significa', 'Como interpretar'], [
        ['A', 'Adequado / permitido', 'Pode seguir com o projeto, respeitando as demais regras.'],
        ['I', 'Inadequado / não permitido', 'Em regra, não pode nesse local/condição.'],
        ['AP', 'Adequado (pequeno porte)', 'Pode, mas normalmente limitado a porte pequeno.'],
        ['AM', 'Adequado (médio porte)', 'Pode, mas normalmente limitado a porte médio.'],
        ['AP/AM', 'Depende do porte', 'Pode, mas depende se o caso é pequeno ou médio.'],
        ['PE', 'Projeto especial', 'Pode exigir análise específica e condições extras no licenciamento.'],
    ]))
    body.append(_table_html(['Porte', 'Faixa (área construída total)'], [
        ['Pequeno', 'até 250 m²'],
        ['Médio', 'de 250,01 m² até 1.000 m²'],
        ['Grande', 'de 1.000,01 m² até 5.000 m²'],
        ['Projeto especial', 'acima de 5.000 m²'],
    ]))
    body.append('</div></div>')

    # 04
    body.append('<hr class="sep"><div class="section-title">🧭 4️⃣ O que essa zona permite neste terreno?</div><div class="section-body">')
    body.append('<p>Todo terreno está inserido em uma zona, e cada zona pode ter regras, restrições e critérios próprios de uso e ocupação. Nas áreas urbanas, essas informações normalmente ajudam a definir o que pode ser construído, quanto pode ocupar no térreo, quanto precisa ficar livre e o porte da edificação. Já em áreas rurais ou em zonas com tratamento especial, nem sempre existem parâmetros urbanísticos numéricos definidos da mesma forma. Nesses casos, a análise ficará restrita aos critérios aplicáveis do Código de Ordenamento Urbano e às demais regras específicas que incidirem sobre a área.</p>')
    body.append(_callout('<div class="subheading">' + _html(zone_desc_title) + '</div><div style="margin-top:8px">' + _html(zone_desc_text) + '</div>'))
    body.append('<p><strong>É essa leitura da zona que ajuda a entender o que pode ser implantado no lote e com qual porte.</strong></p></div>')

    # 05
    body.append('<hr class="sep"><div class="section-title">📏 5️⃣ Regras principais para este terreno</div><div class="section-body">')
    body.append('<p>Depois de entender a zona, o próximo passo é ver as regras básicas do lote.</p><p>Para este terreno, vale olhar principalmente:</p>')
    body.append(_markdown_list(['ocupação máxima no térreo', 'área que precisa ficar livre', 'recuos', 'altura máxima', 'potencial total de construção']))
    body.append('<div class="rule-grid">' + ''.join([
        f'<div class="rule-card"><div class="rule-label">TO máxima</div><div class="rule-value">{_html(_fmt_pct(ctx.get("to_max")))}</div></div>',
        f'<div class="rule-card"><div class="rule-label">TP mínima</div><div class="rule-value">{_html(_fmt_pct(ctx.get("tp_min")))}</div></div>',
        f'<div class="rule-card"><div class="rule-label">IA máximo</div><div class="rule-value">{_html(_fmt_int_or_num(ctx.get("ia_max")))}</div></div>',
        f'<div class="rule-card"><div class="rule-label">IA mínimo</div><div class="rule-value">{_html(ia_min_texto)}</div></div>',
        f'<div class="rule-card"><div class="rule-label">Recuos</div><div class="rule-value">{_html(f"F: {_fmt_m(ctx.get('rec_fr'))} | L: {_fmt_m(ctx.get('rec_lat'))} | Fu: {_fmt_m(ctx.get('rec_fun'))}")}</div></div>',
        f'<div class="rule-card"><div class="rule-label">Altura máxima</div><div class="rule-value">{_html(_fmt_m(ctx.get("gabarito")))}</div></div>',
    ]) + '</div><p class="muted">Essas são as regras que mais impactam o projeto.</p></div>')

    # 06
    body.append('<hr class="sep"><div class="section-title">📐 6️⃣ Quanto posso ocupar no térreo?</div><div class="section-body">')
    if ctx.get('to_max') is None or a_to is None:
        body.append(_callout('Sem TO máxima cadastrada para esta zona/uso.', 'warning'))
    else:
        body.append(f'<p>A zona permite ocupar até <strong>{_html(_fmt_pct(ctx.get("to_max")))}</strong> do terreno no térreo.</p>')
        body.append(_formula_box_html(f'{_fmt_area(area)} × {_fmt_pct(ctx.get("to_max"))} = {_fmt_area(a_to)}'))
        body.append('<p>Esse é o limite máximo permitido pela Taxa de Ocupação (TO).</p>')
        body.append(_callout('<div class="subheading">Opção principal — aproveitando a flexibilidade da lei</div><p style="margin-top:8px">Para residência unifamiliar, a legislação admite zerar o recuo frontal e os recuos laterais, desde que o projeto continue respeitando a TO máxima e a TP mínima.</p><p style="margin-top:8px"><strong>Térreo máximo nesta opção:</strong> ' + _html(_fmt_area(a_op2_max)) + '</p>'))
        if not ctx.get('is_irregular'):
            body.append(_callout(
                '<div class="subheading">Opção alternativa — adotando os recuos da zona</div>'
                f'<p style="margin-top:8px">Frontal: <strong>{_html(_fmt_m(ctx.get("rec_fr")))}</strong></p>'
                f'<p>Laterais: <strong>{_html(_fmt_m(ctx.get("rec_lat")))}</strong> cada</p>'
                f'<p>Fundo: <strong>{_html(_fmt_m(ctx.get("rec_fun")))}</strong></p>'
                f'<p style="margin-top:8px"><strong>Largura útil:</strong> {_html(_fmt_m(ctx.get("w_util")))} | <strong>Profundidade útil:</strong> {_html(_fmt_m(ctx.get("d_util")))}</p>'
                + (f'<p style="margin-top:8px"><strong>{_html(_fmt_m(ctx.get("w_util")))} × {_html(_fmt_m(ctx.get("d_util")))} = {_html(_fmt_area(a_recuos))}</strong></p>' if a_recuos is not None else '')
            ))
        else:
            body.append(_callout('Terreno irregular: como o lote não é retangular, o relatório não calcula a implantação por recuos. Aqui são apresentados os limites legais por TO, TP e IA.', 'warning'))
    body.append('</div>')

    # 07
    body.append('<hr class="sep"><div class="section-title">🌿 7️⃣ Quanto preciso deixar livre?</div><div class="section-body">')
    if ctx.get('tp_min') is None or a_perm_min is None:
        body.append(_callout('Sem TP mínima cadastrada para esta zona/uso.', 'warning'))
    else:
        body.append(f'<p>A zona exige <strong>{_html(_fmt_pct(ctx.get("tp_min")))}</strong> de área permeável.</p>')
        body.append(_formula_box_html(f'{_fmt_area(area)} × {_fmt_pct(ctx.get("tp_min"))} = {_fmt_area(a_perm_min)} obrigatórios permeáveis'))
        tp2 = tp_scenario(a_op2_max)
        if tp2:
            a_rest, a_imperm = tp2
            body.append(_callout(f'<div class="subheading">Cenário pela opção principal</div><p style="margin-top:8px">Usando <strong>{_html(_fmt_area(a_op2_max))}</strong> no térreo, sobra <strong>{_html(_fmt_area(a_rest))}</strong> no lote.</p><p style="margin-top:8px">Desses, <strong>{_html(_fmt_area(a_perm_min))}</strong> devem permitir infiltração no solo e <strong>{_html(_fmt_area(a_imperm))}</strong> podem receber piso impermeável.</p>'))
        tp1 = tp_scenario(ctx.get('a_op1_max'))
        if tp1 and ctx.get('a_op1_max') is not None:
            a_rest, a_imperm = tp1
            body.append(_callout(f'<div class="subheading">Cenário pela opção com recuos da zona</div><p style="margin-top:8px">Usando <strong>{_html(_fmt_area(ctx.get("a_op1_max")))}</strong> no térreo, sobra <strong>{_html(_fmt_area(a_rest))}</strong> no lote.</p><p style="margin-top:8px">Desses, <strong>{_html(_fmt_area(a_perm_min))}</strong> devem permitir infiltração no solo e <strong>{_html(_fmt_area(a_imperm))}</strong> podem receber piso impermeável.</p>'))
    body.append('</div>')

    # 08
    body.append('<hr class="sep"><div class="section-title">🧱 8️⃣ Tipos de piso: o que conta como permeável?</div><div class="section-body">')
    body.append('<p>Nem todo piso externo conta do mesmo jeito na permeabilidade. Veja como a lei trata isso:</p>')
    body.append(_table_html(['Tipo de Piso', 'Percentual considerado permeável'], [[a, b] for a, b in PERMEABILIDADE_ROWS]))
    body.append('<p class="muted">Isso ajuda a entender que nem toda área “livre” do lote conta 100% como permeável.</p></div>')

    # 09
    body.append('<hr class="sep"><div class="section-title">🏢 9️⃣ Posso construir mais andares?</div><div class="section-body">')
    if ctx.get('ia_max') is not None and a_total is not None:
        body.append('<p>Além da ocupação no térreo, a zona também define o potencial construtivo total do lote por meio do Índice de Aproveitamento (IA).</p>')
        body.append(_formula_box_html(f'{_fmt_area(area)} × {_fmt_int_or_num(ctx.get("ia_max"))} = {_fmt_area(a_total)}'))
        body.append('<p>Esse é o total que pode ser distribuído entre térreo e pavimentos superiores, respeitando também os demais parâmetros urbanísticos.</p>')
    if ctx.get('gabarito') is not None:
        body.append(_callout(f'<div class="subheading">Altura máxima da zona</div><p style="margin-top:8px"><strong>{_html(_fmt_m(ctx.get("gabarito")))}</strong></p><p style="margin-top:8px">Exemplo simples: adotando pé-direito médio de 3,00 m por pavimento, isso pode permitir algo próximo de <strong>{_html(str(ctx.get("pav_est") or "-"))} pavimentos</strong>, apenas como referência inicial.</p>'))
    body.append('</div>')

    # 10
    body.append('<hr class="sep"><div class="section-title">🚗 1️⃣0️⃣ Preciso de vagas de estacionamento?</div><div class="section-body">')
    body.append(_callout('<div class="subheading">Estacionamento</div><p style="margin-top:8px">Neste caso, não existe exigência mínima obrigatória de vagas de estacionamento. Essa exigência costuma aparecer em residências multifamiliares e em outras atividades previstas na lei.</p>', 'success'))
    body.append('</div>')

    # 11
    body.append('<hr class="sep"><div class="section-title">📋 1️⃣1️⃣ Quais medidas mínimas os ambientes precisam ter?</div><div class="section-body">')
    body.append('<p>Além das regras do lote, a legislação também traz medidas mínimas para alguns ambientes da edificação.</p>')
    body.append(_table_html(['Ambiente', 'Círculo inscrito', 'Área mínima', 'Iluminação', 'Ventilação', 'Pé-direito', 'Obs.'], [[row[h] for h in ['AMBIENTE', 'CIRCULO INSCRITO', 'AREA MINIMA', 'ILUMINACAO', 'VENTILACAO', 'PE-DIREITO', 'OBS.']] for row in QUADRO_ROWS]))
    body.append(_callout('<div class="subheading">Observações aplicáveis</div>' + _markdown_list(QUADRO_OBS)))
    body.append('</div>')

    # 12
    body.append('<hr class="sep"><div class="section-title">🚶 1️⃣2️⃣ O que preciso saber sobre a calçada?</div><div class="section-body">')
    body.append('<p>A análise não termina dentro do lote. Também existem regras para calçada, acesso ao imóvel, rebaixo de meio-fio e relação do lote com a rua. As figuras abaixo ajudam a visualizar esse padrão.</p>')
    if figures:
        for fig in figures:
            body.append('<div class="figure-card no-break"><img src="' + _html(fig.get('url') or '') + '" alt="' + _html(fig.get('title') or 'Figura') + '"><div class="figure-meta"><div class="figure-title">' + _html(fig.get('title') or 'Figura') + '</div><div class="muted">' + _html(fig.get('caption') or 'Anexo V - LC 90/2023') + '</div></div></div>')
    else:
        body.append(_callout('As figuras do Anexo V não estavam disponíveis para este estudo.', 'warning'))
    body.append('</div>')

    # 13
    body.append('<hr class="sep"><div class="section-title">💡 1️⃣3️⃣ Dicas valiosas</div><div class="section-body">')
    body.append(_callout('<div class="subheading">Flexibilidade de recuos no uso residencial unifamiliar</div><p style="margin-top:8px"><strong>Art. 112.</strong> Será aplicado, para as atividades atrativas de vizinhança de pequeno porte e para o uso residencial unifamiliar, a flexibilidade quanto aos recuos de frente e laterais, podendo zerar, desde que observado o cumprimento da Taxa de Permeabilidade Mínima e da Taxa de Ocupação Máxima da zona em que se encontra.</p><p style="margin-top:8px">👉 <strong>Na prática:</strong> para residência unifamiliar, a legislação admite zerar recuos frontal e laterais, desde que a proposta continue respeitando a <strong>TP mínima</strong> e a <strong>TO máxima</strong> da zona.</p>'))
    body.append(_callout('<div class="subheading">Calçada</div><p style="margin-top:8px">Não existe uma largura única e fixa para toda calçada no município. Quando houver padrão definido no loteamento ou na via, ele deve ser seguido. Quando não houver, a referência costuma ser a calçada já existente no local.</p><div class="subheading" style="margin-top:10px">Piscina</div><p style="margin-top:8px">Piscina não entra como área construída para a Taxa de Ocupação (TO). Mas ela conta como área impermeável para a Taxa de Permeabilidade (TP). Além disso, deve respeitar afastamento mínimo de 0,50 m das divisas.</p>'))
    body.append('</div>')

    # 14
    body.append('<hr class="sep"><div class="section-title">📌 1️⃣4️⃣ Resumo rápido final</div><div class="section-body">')
    body.append('<p><strong>Se você quiser ver só o essencial deste terreno, este é o resumo principal:</strong></p>')
    summary_items = [
        _kv_item('Uso analisado', 'Residência unifamiliar'),
        _kv_item('Zona', zone_desc_title),
        _kv_item('Tipo de lote', str(ctx.get('tipo_lote') or '-')),
        _kv_item('Via', str(ctx.get('via') or '-')),
        _kv_item('Tipo de via', str(ctx.get('via_tipo') or '-')),
        _kv_item('TO máxima', _fmt_pct(ctx.get('to_max'))),
        _kv_item('TP mínima', _fmt_pct(ctx.get('tp_min'))),
        _kv_item('IA máximo', _fmt_int_or_num(ctx.get('ia_max'))),
        _kv_item('Altura máxima', _fmt_m(ctx.get('gabarito'))),
        _kv_item('Área máxima no térreo pela TO', _fmt_area(a_to)),
        _kv_item('Área permeável mínima', _fmt_area(a_perm_min)),
        _kv_item('Área total máxima estimada', _fmt_area(a_total)),
    ]
    if ctx.get('built_ground') is not None and ctx.get('a_adotada') is not None:
        summary_items += [
            _kv_item('Área pretendida informada', _fmt_area(ctx.get('built_ground'))),
            _kv_item('Área adotada no relatório', _fmt_area(ctx.get('a_adotada'))),
        ]
    body.append('<div class="kv-grid">' + ''.join(summary_items) + '</div>')
    body.append('<p>👉 <strong>Em resumo:</strong> você pode ocupar até a TO máxima da zona no térreo; precisa manter pelo menos a TP mínima do terreno permeável; a construção pode chegar até o IA máximo vezes a área do lote no total; e a altura deve respeitar o limite da zona.</p>')
    body.append('</div>')

    # 15
    body.append('<hr class="sep"><div class="section-title">🏛️ 1️⃣5️⃣ O que acontece depois desta etapa?</div><div class="section-body">')
    body.append('<p>Após a finalização dos projetos, será necessário dar entrada na documentação junto à <strong>Prefeitura</strong> para obter o <strong>alvará de construção</strong>.</p>')
    body.append('<p>De forma geral, esse processo pode seguir por <strong>duas vias</strong>:</p>')
    body.append(_markdown_list([
        'Alvará de Construção Simplificado → voltado para casos mais simples e de menor porte;',
        'Alvará de Construção (Obra Nova) → usado quando a obra exige análise técnica mais completa e documentação complementar.',
    ]))
    body.append('<p>Abaixo, apresentamos um resumo dos dois caminhos e um checklist básico dos itens que normalmente precisam ser providenciados.</p>')
    body.append(_callout('<div class="subheading">📄 Alvará de Construção Simplificado</div><p style="margin-top:8px">O <strong>Alvará de Construção Simplificado</strong> é uma forma mais rápida de licenciamento, voltada para casos mais simples. Ele costuma ser usado para <strong>residência unifamiliar</strong> e para <strong>comércio/serviços de pequeno porte</strong>, com área construída de até <strong>250,00 m²</strong>.</p><p style="margin-top:8px">A lógica desse alvará é mais enxuta e autodeclaratória, mas isso não elimina a necessidade de apresentar os documentos corretos e atender às exigências urbanísticas e técnicas do Município.</p><div class="subheading" style="margin-top:10px">✅ Checklist — documentos e itens principais</div>' + '<ul class="plain-list checklist">' + ''.join(f'<li>{_html(x)}</li>' for x in [
        'Documento de identidade do requerente ou representante legal', 'CPF ou CNPJ', 'Matrícula atualizada do imóvel ou documento equivalente', 'Certidão negativa de IPTU', 'Parecer favorável de Adequabilidade Locacional', 'Tabela com índices urbanísticos e áreas da edificação', 'Projeto arquitetônico em arquivo digital', 'ART/RRT do responsável técnico', 'Termo de responsabilidade do responsável técnico', 'Termo de responsabilidade do proprietário', 'Isenção da licença ambiental'
    ]) + '</ul><div class="subheading" style="margin-top:10px">📌 Atenção</div><ul class="plain-list checklist">' + ''.join(f'<li>{_html(x)}</li>' for x in [
        'Confirmar se o caso realmente se enquadra como simplificado', 'Conferir se a área construída está dentro do limite permitido', 'Protocolar o pedido com antecedência mínima indicada pelo procedimento', 'Verificar se todos os arquivos digitais estão prontos e legíveis'
    ]) + '</ul>'))
    body.append(_callout('<div class="subheading">🏗️ Alvará de Construção (Obra Nova)</div><p style="margin-top:8px">O <strong>Alvará de Construção (Obra Nova)</strong> é o caminho regular de licenciamento para obras novas que exigem análise técnica completa da Prefeitura. Ele é mais detalhado e costuma ser necessário em casos que não se enquadram no procedimento simplificado ou que exigem documentação complementar.</p><p style="margin-top:8px">Esse tipo de alvará pede uma conferência mais ampla do projeto, incluindo aspectos urbanísticos, arquitetônicos, hidrossanitários, ambientais e, em alguns casos, exigências de outros órgãos.</p><div class="subheading" style="margin-top:10px">✅ Checklist — documentos principais</div>' + '<ul class="plain-list checklist">' + ''.join(f'<li>{_html(x)}</li>' for x in [
        'Requerimento único', 'Documento de identidade do requerente ou representante legal', 'CPF ou CNPJ', 'Matrícula atualizada do imóvel', 'Autorização do proprietário, quando necessária', 'BCI', 'ART/RRT com comprovante de pagamento', 'Projeto arquitetônico assinado', 'Projeto hidrossanitário', 'Memorial de cálculo e drenagem pluvial', 'Declaração do SAAE sobre rede de esgoto, quando necessária'
    ]) + '</ul><div class="subheading" style="margin-top:10px">✅ Checklist — documentos adicionais que podem ser exigidos</div><ul class="plain-list checklist">' + ''.join(f'<li>{_html(x)}</li>' for x in [
        'Aprovação do Corpo de Bombeiros', 'Aprovação do IPHAN, quando o imóvel estiver em ZEIP', 'Licenciamento ambiental ou termo de isenção', 'PGRSCC', 'Autorização do COMAR, quando aplicável', 'Aprovação do DNIT ou SOP, quando houver acesso por rodovia', 'EIV, quando exigido pela legislação'
    ]) + '</ul><div class="subheading" style="margin-top:10px">📌 Atenção</div><ul class="plain-list checklist">' + ''.join(f'<li>{_html(x)}</li>' for x in [
        'Confirmar se o caso realmente exige alvará regular de obra nova', 'Conferir se há exigência de documentos complementares por localização ou tipologia', 'Verificar se o imóvel está em área com proteção especial', 'Conferir se o projeto atende às exigências técnicas antes do protocolo'
    ]) + '</ul>'))
    body.append('</div>')

    # 16
    body.append('<hr class="sep"><div class="section-title">✅ 1️⃣6️⃣ Fechamento final</div><div class="section-body">')
    body.append(_callout('Este relatório foi pensado para ajudar a entender o terreno de forma mais simples.<br><br>Na etapa de projeto e aprovação, ainda será preciso conferir os detalhes completos no setor de licenciamento de obras da prefeitura.'))
    body.append('</div>')

    body.append('<div class="footer-note">Documento gerado pelo Viabilidade Fácil com base no mesmo conteúdo exibido na tela do relatório urbanístico.</div></body></html>')
    return ''.join(body)


def _generate_html_report_pdf_bytes(calc: Dict[str, Any], session_state: Dict[str, Any]) -> bytes:
    if HTML is None:
        raise RuntimeError("WeasyPrint nao esta disponivel no ambiente.")
    payload = build_report_payload(calc, session_state)
    ctx = _extract_context(calc, session_state)
    html = _render_unifamiliar_report_html(ctx, payload)
    base_url = str(Path(__file__).resolve().parent.parent)
    return HTML(string=html, base_url=base_url).write_pdf()


def _render_html_fallback_warning(pdf: _ReportPDF, reason: str) -> None:
    _section_title(pdf, "AVISO SOBRE A GERACAO DO PDF")
    _status_box(
        pdf,
        "Nao foi possivel renderizar o PDF em HTML com a identidade visual reforcada. O sistema gerou automaticamente a versao de contingencia para nao interromper o download.",
        False,
    )
    _paragraph(pdf, "Motivo tecnico identificado:", bold=True)
    _paragraph(pdf, reason, color=(153, 52, 52))
    _paragraph(pdf, "Acao recomendada: verificar a instalacao do WeasyPrint/dependencias e gerar o PDF novamente.")
    pdf.ln(1)


def _generate_legacy_report_pdf_bytes(calc: Dict[str, Any], session_state: Dict[str, Any], *, html_failure_reason: str | None = None) -> bytes:
    payload = build_report_payload(calc, session_state)
    pdf = _ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.set_margins(14, 24, 14)
    pdf.add_page()

    ctx = _extract_context(calc, session_state)
    _meta_header(pdf, ctx, payload["generated_at"])
    if html_failure_reason:
        _render_html_fallback_warning(pdf, html_failure_reason)
    _render_localizacao_indices_analise(pdf, ctx)
    _render_zone_description_block(pdf, ctx)
    _render_relatorio_narrativo(pdf, ctx)
    _render_quadro_tecnico(pdf)
    _render_dicas_valiosas(pdf, is_corner=bool(ctx["is_corner"]))
    _render_figuras(pdf, payload.get("figures", []))

    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(_full_width(pdf), 4.2, _sanitize("Documento gerado pelo Viabilidade Facil com base nos parametros urbanisticos exibidos no relatorio do sistema."))
    result = pdf.output(dest="S")
    if isinstance(result, bytearray):
        return bytes(result)
    if isinstance(result, bytes):
        return result
    return result.encode("latin-1", errors="replace")
def build_report_payload(calc: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
    rule = calc.get("rule") or {}
    return {
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "calc": calc,
        "session_state": session_state,
        "figures": filter_figuras_by_lot_type(_extract_figures_from_rule(rule), is_corner=bool(session_state.get("lot_is_corner") or calc.get("lot_is_corner"))),
    }


def generate_report_pdf_bytes(calc: Dict[str, Any], session_state: Dict[str, Any]) -> bytes:
    use_code = str((calc or {}).get("use_type_code") or "RES_UNI").upper().strip()
    if use_code.startswith("RES_UNI"):
        try:
            return _generate_html_report_pdf_bytes(calc, session_state)
        except Exception as exc:
            reason = str(exc).strip() or exc.__class__.__name__
            return _generate_legacy_report_pdf_bytes(calc, session_state, html_failure_reason=reason)
    return _generate_legacy_report_pdf_bytes(calc, session_state)
