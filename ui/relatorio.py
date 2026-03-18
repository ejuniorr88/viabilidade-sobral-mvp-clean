
from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from core.zone_descriptions import fetch_zone_description

# Âncoras críticas preservadas para blindagem dos testes existentes
from .relatorio_blocks import render_quadro_tecnico, render_dicas_valiosas, render_figuras_anexo_v, render_multifamiliar_guia
from .relatorio_blocks.unifamiliar import render_relatorio_unifamiliar
from .relatorio_blocks.multifamiliar import render_relatorio_multifamiliar


def _safe_float(v: Any) -> float | None:
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None


def _fmt_num(v: Any, dec: int = 2) -> str:
    try:
        if v is None:
            return "—"
        f = float(v)
        return f"{f:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(v)


def _fmt_pct(v: Any, dec: int = 1) -> str:
    try:
        if v is None:
            return "—"
        f = float(v)
        return f"{f:.{dec}f}%"
    except Exception:
        return "—"


def _to_pct(rule: Dict[str, Any], key_pct: str, key_frac: str) -> float | None:
    v = rule.get(key_pct, None)
    if v is not None:
        try:
            return float(v)
        except Exception:
            pass
    v = rule.get(key_frac, None)
    if v is None:
        return None
    try:
        f = float(v)
        return f * 100.0 if 0 <= f <= 1.0 else f
    except Exception:
        return None


def _lot_type_text(calc: Dict[str, Any]) -> str:
    if bool(st.session_state.get("lot_is_corner") or calc.get("lot_is_corner")):
        return "Esquina"
    return "Meio de quadra"


def render_zone_description_section(calc: Dict[str, Any]) -> None:
    if not isinstance(calc, dict) or not calc.get("ok"):
        return

    rule = calc.get("rule") or {}
    zone_sigla = calc.get("zone_sigla") or calc.get("zone_lookup") or calc.get("zone") or rule.get("zone_sigla") or ""
    subzone_code = calc.get("subzone_code") or rule.get("subzone_code") or "PADRAO"
    zone_label = calc.get("zone") or calc.get("zone_display") or calc.get("zone_label_raw") or rule.get("zone_sigla") or ""

    try:
        desc = fetch_zone_description(str(zone_sigla or ""), str(subzone_code or "PADRAO"), str(zone_label or ""))
    except Exception:
        desc = None

    if not desc or not desc.get("description_text"):
        return

    title = desc.get("title") or "Sobre esta zona"
    st.markdown("---")
    st.subheader("Descrição da zona")
    st.markdown(f"**{title}**")
    st.markdown(str(desc.get("description_text")))


def _build_base_context(calc: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
    area_terreno = float(calc.get("lot_area_m2") or 0.0)
    testada = float(st.session_state.get("lot_testada_m") or calc.get("lot_testada_m") or 0.0)
    profundidade = float(st.session_state.get("lot_profundidade_m") or calc.get("lot_profundidade_m") or 0.0)
    to_max = _to_pct(rule, "to_max_pct", "to_max")
    tp_min = _to_pct(rule, "tp_min_pct", "tp_min")
    ia_max = rule.get("ia_max")
    gabarito_m = rule.get("gabarito_m")

    try:
        area_total_max = area_terreno * float(ia_max) if ia_max is not None else None
    except Exception:
        area_total_max = None

    zona_nome_completo = calc.get("zone_zona_sigla_text") or calc.get("zone_label_raw") or calc.get("zone") or "—"
    via = calc.get("via_nome") or calc.get("street_name") or "—"
    via_tipo = calc.get("via_tipo") or calc.get("street_type") or "—"

    try:
        desc = fetch_zone_description(
            str(calc.get("zone_sigla") or calc.get("zone_lookup") or calc.get("zone") or rule.get("zone_sigla") or ""),
            str(calc.get("subzone_code") or rule.get("subzone_code") or "PADRAO"),
            str(calc.get("zone") or calc.get("zone_display") or calc.get("zone_label_raw") or rule.get("zone_sigla") or ""),
        )
    except Exception:
        desc = None

    return {
        "localizacao": {
            "uso_label": calc.get("use_type_label") or calc.get("use_label") or calc.get("use_type_code") or "—",
            "area_terreno": f"{_fmt_num(area_terreno)} m²" if area_terreno else "—",
            "dimensoes": f"{_fmt_num(testada)} m × {_fmt_num(profundidade)} m" if testada and profundidade else "—",
            "zona": calc.get("zone") or calc.get("zone_sigla") or "—",
            "subzona": calc.get("subzone_code") or rule.get("subzone_code") or "PADRAO",
            "tipo_lote": _lot_type_text(calc),
            "nome_via": via,
            "tipo_via": via_tipo,
        },
        "viabilidade": {
            "resultado_zona": calc.get("resultado_zona") or calc.get("zone_result") or "Verificar pela zona carregada",
            "resultado_via": calc.get("resultado_via") or calc.get("via_result") or ("Via local / sem restrição adicional" if str(via_tipo).strip() else "—"),
            "resultado_final": calc.get("resultado_final") or ("Viável na análise inicial" if calc.get("ok") else "Não viável"),
            "texto_apoio": calc.get("texto_apoio") or "Resultado inicial para leitura rápida. A conferência final continua dependendo do licenciamento.",
        },
        "zona": {
            "zona": calc.get("zone") or calc.get("zone_sigla") or "—",
            "zona_nome_completo": zona_nome_completo,
            "zona_texto_o_que_e": (desc or {}).get("title") or "Descrição da zona carregada no sistema.",
            "zona_texto_pratico": (desc or {}).get("description_text") or "Sem texto adicional cadastrado para esta zona.",
            "nome_via": via,
            "tipo_via": via_tipo,
        },
        "parametros": {
            "to_max": _fmt_pct(to_max) if to_max is not None else "—",
            "tp_min": _fmt_pct(tp_min) if tp_min is not None else "—",
            "ia_max": ia_max if ia_max is not None else "—",
            "ia_min_texto": rule.get("ia_min") if rule.get("ia_min") is not None else "—",
            "recuo_frontal": f"{_fmt_num(rule.get('recuo_frontal_m') or 0)} m",
            "recuo_lateral_texto": f"{_fmt_num(rule.get('recuo_lateral_m') or 0)} m",
            "recuo_fundos": f"{_fmt_num(rule.get('recuo_fundos_m') or 0)} m",
            "altura_max": f"{_fmt_num(gabarito_m)} m" if gabarito_m is not None else "—",
        },
        "ia": {
            "area_terreno": f"{_fmt_num(area_terreno)} m²" if area_terreno else "—",
            "ia_max": ia_max if ia_max is not None else "—",
            "area_total_max": f"{_fmt_num(area_total_max)} m²" if area_total_max is not None else "—",
            "altura_max": f"{_fmt_num(gabarito_m)} m" if gabarito_m is not None else "—",
        },
        "rule": rule,
    }


def _build_unifamiliar_context(calc: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
    ctx = _build_base_context(calc, rule)
    area_terreno = float(calc.get("lot_area_m2") or 0.0)
    testada = float(st.session_state.get("lot_testada_m") or calc.get("lot_testada_m") or 0.0)
    profundidade = float(st.session_state.get("lot_profundidade_m") or calc.get("lot_profundidade_m") or 0.0)
    to_max = _to_pct(rule, "to_max_pct", "to_max")
    tp_min = _to_pct(rule, "tp_min_pct", "tp_min")
    rec_fr = float(rule.get("recuo_frontal_m") or 0.0)
    rec_lat = float(rule.get("recuo_lateral_m") or 0.0)
    rec_fun = float(rule.get("recuo_fundos_m") or 0.0)

    area_to_max = area_terreno * (to_max / 100.0) if area_terreno and to_max is not None else None
    largura_util = testada - 2 * rec_lat
    profundidade_util = profundidade - rec_fr - rec_fun
    area_impl = largura_util * profundidade_util if largura_util > 0 and profundidade_util > 0 else None
    area_max_alinh = min(area_to_max, (testada * (profundidade - rec_fun))) if area_to_max is not None and testada > 0 and profundidade > rec_fun else area_to_max
    area_perm_min = area_terreno * (tp_min / 100.0) if area_terreno and tp_min is not None else None
    area_rest1 = area_terreno - area_impl if area_impl is not None else None
    area_rest2 = area_terreno - area_max_alinh if area_max_alinh is not None else None
    area_imperm1 = area_rest1 - area_perm_min if area_rest1 is not None and area_perm_min is not None else None
    area_imperm2 = area_rest2 - area_perm_min if area_rest2 is not None and area_perm_min is not None else None

    ctx["ocupacao"] = {
        "area_terreno": ctx["localizacao"]["area_terreno"],
        "to_max": ctx["parametros"]["to_max"],
        "area_to_max": f"{_fmt_num(area_to_max)} m²" if area_to_max is not None else "—",
        "recuo_frontal": ctx["parametros"]["recuo_frontal"],
        "recuo_lateral_texto": ctx["parametros"]["recuo_lateral_texto"],
        "recuo_fundos": ctx["parametros"]["recuo_fundos"],
        "largura_util": f"{_fmt_num(largura_util)} m" if largura_util is not None else "—",
        "profundidade_util": f"{_fmt_num(profundidade_util)} m" if profundidade_util is not None else "—",
        "area_implantacao_recuos": f"{_fmt_num(area_impl)} m²" if area_impl is not None else "—",
        "implantacao_alinhamento_status": "Sim" if area_max_alinh is not None else "Não",
        "area_max_alinhamento": f"{_fmt_num(area_max_alinh)} m²" if area_max_alinh is not None else "—",
    }
    ctx["permeabilidade"] = {
        "area_terreno": ctx["localizacao"]["area_terreno"],
        "tp_min": ctx["parametros"]["tp_min"],
        "area_permeavel_min": f"{_fmt_num(area_perm_min)} m²" if area_perm_min is not None else "—",
        "area_ocupada_op1": f"{_fmt_num(area_impl)} m²" if area_impl is not None else "—",
        "area_restante_op1": f"{_fmt_num(area_rest1)} m²" if area_rest1 is not None else "—",
        "area_impermeavel_op1": f"{_fmt_num(area_imperm1)} m²" if area_imperm1 is not None else "—",
        "area_ocupada_op2": f"{_fmt_num(area_max_alinh)} m²" if area_max_alinh is not None else "—",
        "area_restante_op2": f"{_fmt_num(area_rest2)} m²" if area_rest2 is not None else "—",
        "area_impermeavel_op2": f"{_fmt_num(area_imperm2)} m²" if area_imperm2 is not None else "—",
    }
    ctx["vagas"] = {"exige_vagas_texto": "Não há exigência mínima obrigatória para residência unifamiliar.", "qtd_vagas": "—"}
    return ctx


def _build_multifamiliar_context(calc: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
    ctx = _build_base_context(calc, rule)
    ctx["tipo_multifamiliar"] = calc.get("multi_tipo") or calc.get("tipo_multifamiliar") or "R2.1"
    return ctx


def render_relatorio_section(calc: Dict[str, Any]) -> None:
    st.subheader("6) Relatório Urbanístico")

    if not isinstance(calc, dict) or not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar o relatório.")
        return

    rule = calc.get("rule") or {}
    uso = str(calc.get("use_type_code") or "RES_UNI")

    render_zone_description_section(calc)

    if uso.startswith("RES_MULTI_"):
        contexto = _build_multifamiliar_context(calc, rule)
        render_relatorio_multifamiliar(contexto)
    else:
        contexto = _build_unifamiliar_context(calc, rule)
        render_relatorio_unifamiliar(contexto)

    with st.expander("Ver regra completa (JSON)"):
        st.json(rule)
