from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.request import urlopen

from fpdf import FPDF


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


# =============================
# Figuras do Anexo V
# =============================

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
        with urlopen(url, timeout=12) as resp:
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


# =============================
# Montagem do conteúdo
# =============================

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

    # Quadro técnico – parâmetros dos ambientes
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
            "Não há, na legislação municipal, uma medida única e fixa para a largura dos passeios. Quando existir, deve-se adotar o padrão definido no projeto aprovado do loteamento e/ou nas diretrizes urbanísticas da via. Na ausência dessa previsão, utiliza-se como referência o passeio já implantado no logradouro, garan
