from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence
from urllib.request import urlopen

from fpdf import FPDF

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
    }


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


def _render_dicas_valiosas(pdf: _ReportPDF) -> None:
    _section_title(pdf, "DICAS VALIOSAS")
    for titulo, texto in DICAS_VALIOSAS:
        pdf.set_font("Helvetica", "B", 10.8)
        pdf.multi_cell(_full_width(pdf), 5.4, _sanitize(titulo + ":"))
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

    ctx = _extract_context(calc, session_state)
    _meta_header(pdf, ctx, payload["generated_at"])
    _render_localizacao_indices_analise(pdf, ctx)
    _render_relatorio_narrativo(pdf, ctx)
    _render_quadro_tecnico(pdf)
    _render_dicas_valiosas(pdf)
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
