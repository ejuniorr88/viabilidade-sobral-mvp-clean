from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List

from fpdf import FPDF


def _safe_str(value: Any, default: str = "—") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _safe_float(value: Any) -> float | None:
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


def _to_pct(rule: Dict[str, Any], key_pct: str, key_frac: str) -> float | None:
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


def _build_rows(calc: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, List[tuple[str, str]]]:
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

    notes: List[tuple[str, str]] = []
    if calc.get("err"):
        notes.append(("Observação", _safe_str(calc.get("err"))))

    if is_irregular:
        notes.append(
            (
                "Lote irregular",
                "Em lote irregular, a implantação final pode ser reduzida por recuos, forma do lote, alinhamento, servidões e exigências do licenciamento.",
            )
        )

    notes.append(
        (
            "Piscinas e áreas impermeáveis",
            "Piscinas não entram na área construída para TO, mas contam como área impermeável para TP e devem respeitar afastamento mínimo de 0,50 m das divisas.",
        )
    )
    notes.append(
        (
            "Calçadas",
            "A largura da calçada deve seguir o loteamento aprovado, diretrizes municipais ou o alinhamento existente da via, observando o licenciamento local.",
        )
    )

    return {
        "identification": identification,
        "parameters": parameters,
        "calculations": calculations,
        "notes": notes,
    }


class _ReportPDF(FPDF):
    def header(self) -> None:
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 8, _sanitize("Viabilidade Fácil — Relatório Urbanístico"), ln=True)
        self.ln(2)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.cell(0, 6, _sanitize(f"Página {self.page_no()}"), align="C")



def _render_section(pdf: _ReportPDF, title: str, rows: List[tuple[str, str]]) -> None:
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, _sanitize(title), ln=True)
    pdf.set_font("Helvetica", "", 10)
    for label, value in rows:
        pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(0, 6, _sanitize(f"{label}:"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, _sanitize(value), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)



def build_report_payload(calc: Dict[str, Any], session_state: Dict[str, Any]) -> Dict[str, Any]:
    rows = _build_rows(calc, session_state)
    return {
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "title": "Relatório Urbanístico",
        "sections": rows,
    }



def generate_report_pdf_bytes(calc: Dict[str, Any], session_state: Dict[str, Any]) -> bytes:
    payload = build_report_payload(calc, session_state)

    pdf = _ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.set_margins(14, 14, 14)
    pdf.add_page()

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _sanitize(f"Emitido em: {payload['generated_at']}"), ln=True)
    pdf.ln(2)

    sections: Dict[str, List[tuple[str, str]]] = payload["sections"]
    _render_section(pdf, "1. Identificação da análise", sections["identification"])
    _render_section(pdf, "2. Parâmetros urbanísticos", sections["parameters"])
    _render_section(pdf, "3. Síntese da análise", sections["calculations"])
    _render_section(pdf, "4. Observações importantes", sections["notes"])

    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(
        0,
        5,
        _sanitize(
            "Este PDF foi estruturado para futura integração com histórico na área do cliente, mantendo a geração separada do armazenamento.")
    )

    result = pdf.output(dest="S")
    if isinstance(result, bytearray):
        return bytes(result)
    if isinstance(result, bytes):
        return result
    return result.encode("latin-1", errors="replace")
