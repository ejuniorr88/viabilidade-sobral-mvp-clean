from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from core.zone_descriptions import fetch_zone_description
from .relatorio_blocks import render_quadro_tecnico, render_dicas_valiosas, render_figuras_anexo_v, render_multifamiliar_guia
from .relatorio_blocks.shared import (
    render_header_relatorio,
    render_tabela_localizacao,
    render_tabela_resultado_viabilidade,
    render_descricao_zona,
    render_fechamento_final,
)
from .relatorio_blocks.unifamiliar import (
    render_tabela_resumo_rapido_unifamiliar,
    render_tabela_regras_principais_unifamiliar,
    render_tabela_ocupacao_terreo_unifamiliar,
    render_tabela_permeabilidade_unifamiliar,
    render_tabela_tipos_piso,
    render_tabela_ia_unifamiliar,
    render_tabela_vagas_unifamiliar,
    render_relatorio_unifamiliar,
)
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
        return f"{float(v):.{dec}f}%"
    except Exception:
        return "—"



def _to_pct(rule: Dict[str, Any], key_pct: str, key_frac: str) -> float | None:
    v = rule.get(key_pct)
    if v is not None:
        try:
            return float(v)
        except Exception:
            pass
    v = rule.get(key_frac)
    if v is None:
        return None
    try:
        f = float(v)
        return f * 100.0 if 0 <= f <= 1.0 else f
    except Exception:
        return None



def _use_label(use_code: str) -> str:
    mapping = {
        "RES_UNI": "residência unifamiliar",
        "RES_MULTI_R21": "residência multifamiliar R2.1",
        "RES_MULTI_R22": "residência multifamiliar R2.2",
        "RES_MULTI_R3": "residência multifamiliar R3",
    }
    return mapping.get(str(use_code or "").upper(), str(use_code or "—"))



def _zone_desc_payload(calc: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
    zone_sigla = calc.get("zone_sigla") or calc.get("zone_lookup") or calc.get("zone") or rule.get("zone_sigla") or ""
    subzone_code = calc.get("subzone_code") or rule.get("subzone_code") or "PADRAO"
    zone_label = calc.get("zone") or calc.get("zone_display") or calc.get("zone_label_raw") or rule.get("zone_sigla") or ""

    desc = None
    try:
        desc = fetch_zone_description(str(zone_sigla), str(subzone_code), str(zone_label))
    except Exception:
        desc = None

    return {
        "zona": zone_sigla or zone_label or "—",
        "zona_nome_completo": (desc or {}).get("title") or zone_label or zone_sigla or "—",
        "zona_texto_o_que_e": (desc or {}).get("title") or f"{zone_sigla} — zona urbana do município",
        "zona_texto_pratico": (desc or {}).get("description_text") or "Esta zona ajuda a definir o que pode ser feito no terreno e quais limites precisam ser respeitados.",
        "nome_via": calc.get("via_nome") or calc.get("street_name") or "—",
        "tipo_via": calc.get("via_tipo") or calc.get("street_type") or "—",
    }



def render_zone_description_section(calc: Dict[str, Any]) -> None:
    """Mantida por blindagem antiga; delega para o novo bloco compartilhado."""
    if not isinstance(calc, dict) or not calc.get("ok"):
        return
    rule = calc.get("rule") or {}
    render_descricao_zona(_zone_desc_payload(calc, rule))



def _build_localizacao(calc: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "uso_label": _use_label(calc.get("use_type_code") or "RES_UNI"),
        "area_terreno": f"{_fmt_num(calc.get('lot_area_m2') or 0)} m²",
        "dimensoes": f"{_fmt_num(st.session_state.get('lot_front_m') or 0)} m × {_fmt_num(st.session_state.get('lot_depth_m') or 0)} m",
        "zona": calc.get("zone") or calc.get("zone_sigla") or "—",
        "subzona": calc.get("subzone_code") or rule.get("subzone_code") or "PADRAO",
        "tipo_lote": "Esquina" if st.session_state.get("lot_is_corner") else "Meio de quadra",
        "nome_via": calc.get("via_nome") or calc.get("street_name") or "—",
        "tipo_via": calc.get("via_tipo") or calc.get("street_type") or "—",
    }



def _build_viabilidade(calc: Dict[str, Any]) -> Dict[str, Any]:
    via_tipo = str(calc.get("via_tipo") or calc.get("street_type") or "").lower()
    if via_tipo and "local" in via_tipo:
        resultado_via = "Via local / sem restrição adicional"
    elif via_tipo:
        resultado_via = f"{calc.get('via_tipo') or calc.get('street_type')} / pode influenciar o enquadramento"
    else:
        resultado_via = "Sem informação de via"

    return {
        "resultado_zona": "Verificar pela zona carregada",
        "resultado_via": resultado_via,
        "resultado_final": "Viável na análise inicial",
        "texto_apoio": "Resultado inicial para leitura rápida. A conferência final continua dependendo do licenciamento.",
    }



def _build_parametros(calc: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
    rec_fr = float(rule.get("recuo_frontal_m") or 0.0)
    rec_lat = float(rule.get("recuo_lateral_m") or 0.0)
    rec_fun = float(rule.get("recuo_fundos_m") or 0.0)
    gabarito_m = rule.get("gabarito_m")
    return {
        "to_max": _fmt_pct(_to_pct(rule, "to_max_pct", "to_max")),
        "tp_min": _fmt_pct(_to_pct(rule, "tp_min_pct", "tp_min")),
        "ia_max": str(rule.get("ia_max") if rule.get("ia_max") is not None else "—"),
        "ia_min_texto": str(rule.get("ia_min") if rule.get("ia_min") is not None else "—"),
        "recuo_frontal": f"{_fmt_num(rec_fr)} m",
        "recuo_lateral_texto": f"{_fmt_num(rec_lat)} m",
        "recuo_fundos": f"{_fmt_num(rec_fun)} m",
        "altura_max": f"{_fmt_num(gabarito_m)} m" if gabarito_m is not None else "—",
    }



def _build_unifamiliar_context(calc: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
    A = float(calc.get("lot_area_m2") or 0.0)
    W = float(st.session_state.get("lot_front_m") or 0.0)
    D = float(st.session_state.get("lot_depth_m") or 0.0)
    to_max = _to_pct(rule, "to_max_pct", "to_max")
    tp_min = _to_pct(rule, "tp_min_pct", "tp_min")
    ia_max = rule.get("ia_max")
    rec_fr = float(rule.get("recuo_frontal_m") or 0.0)
    rec_lat = float(rule.get("recuo_lateral_m") or 0.0)
    rec_fun = float(rule.get("recuo_fundos_m") or 0.0)
    gabarito_m = rule.get("gabarito_m")

    A_to = A * (to_max / 100.0) if (A and to_max is not None) else None
    A_perm_min = A * (tp_min / 100.0) if (A and tp_min is not None) else None
    A_total = A * float(ia_max) if (A and ia_max is not None) else None

    W_util = W - 2 * rec_lat
    D_util = D - rec_fr - rec_fun
    A_recuos = (W_util * D_util) if (W_util > 0 and D_util > 0) else None
    A_op1_max = min(A_to, A_recuos) if (A_to is not None and A_recuos is not None) else None
    A_fundo = (W * (D - rec_fun)) if (W > 0 and D > rec_fun) else None
    A_op2_max = min(A_to, A_fundo) if (A_to is not None and A_fundo is not None) else A_to

    def _tp_scenario(a_terreo: float | None):
        if a_terreo is None or A_perm_min is None:
            return None
        a_rest = A - a_terreo
        a_imperm = a_rest - A_perm_min
        return a_rest, a_imperm

    tp1 = _tp_scenario(A_op1_max)
    tp2 = _tp_scenario(A_op2_max)

    return {
        "localizacao": _build_localizacao(calc, rule),
        "viabilidade": _build_viabilidade(calc),
        "zona": _zone_desc_payload(calc, rule),
        "parametros": _build_parametros(calc, rule),
        "ocupacao": {
            "area_terreno": f"{_fmt_num(A)} m²",
            "to_max": _fmt_pct(to_max),
            "area_to_max": f"{_fmt_num(A_to)} m²" if A_to is not None else "—",
            "recuo_frontal": f"{_fmt_num(rec_fr)} m",
            "recuo_lateral_texto": f"{_fmt_num(rec_lat)} m cada",
            "recuo_fundos": f"{_fmt_num(rec_fun)} m",
            "largura_util": f"{_fmt_num(W_util)} m",
            "profundidade_util": f"{_fmt_num(D_util)} m",
            "area_implantacao_recuos": f"{_fmt_num(A_recuos)} m²" if A_recuos is not None else "—",
            "implantacao_alinhamento_status": "Sim" if A_op2_max is not None else "Não",
            "area_max_alinhamento": f"{_fmt_num(A_op2_max)} m²" if A_op2_max is not None else "—",
        },
        "permeabilidade": {
            "area_terreno": f"{_fmt_num(A)} m²",
            "tp_min": _fmt_pct(tp_min),
            "area_permeavel_min": f"{_fmt_num(A_perm_min)} m²" if A_perm_min is not None else "—",
            "area_ocupada_op1": f"{_fmt_num(A_op1_max)} m²" if A_op1_max is not None else "—",
            "area_restante_op1": f"{_fmt_num(tp1[0])} m²" if tp1 else "—",
            "area_impermeavel_op1": f"{_fmt_num(tp1[1])} m²" if tp1 else "—",
            "area_ocupada_op2": f"{_fmt_num(A_op2_max)} m²" if A_op2_max is not None else "—",
            "area_restante_op2": f"{_fmt_num(tp2[0])} m²" if tp2 else "—",
            "area_impermeavel_op2": f"{_fmt_num(tp2[1])} m²" if tp2 else "—",
        },
        "ia": {
            "area_terreno": f"{_fmt_num(A)} m²",
            "ia_max": str(ia_max if ia_max is not None else "—"),
            "area_total_max": f"{_fmt_num(A_total)} m²" if A_total is not None else "—",
            "altura_max": f"{_fmt_num(gabarito_m)} m" if gabarito_m is not None else "—",
        },
        "vagas": {
            "exige_vagas_texto": "Não há exigência mínima obrigatória de vagas para residência unifamiliar.",
            "qtd_vagas": "—",
        },
    }



def render_relatorio_section(calc: Dict[str, Any]) -> None:
    st.subheader("6) Relatório Urbanístico")

    if not isinstance(calc, dict) or not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar o relatório.")
        return

    rule = calc.get("rule") or {}
    uso = str(calc.get("use_type_code") or "RES_UNI")

    if uso.startswith("RES_MULTI_") and calc.get("project_mode") == "GUIA_FASE_1":
        contexto = {
            "localizacao": _build_localizacao(calc, rule),
            "viabilidade": _build_viabilidade(calc),
            "zona": _zone_desc_payload(calc, rule),
            "parametros": _build_parametros(calc, rule),
            "tipo_multifamiliar": (calc.get("multi_tipo") or "R2.1"),
        }
        render_relatorio_multifamiliar(contexto)
        render_multifamiliar_guia(calc=calc, rule=rule, is_irregular=bool(st.session_state.get("lot_is_irregular", False)))
        render_dicas_valiosas()
        render_quadro_tecnico()
        render_figuras_anexo_v(rule)
        render_fechamento_final("multifamiliar")
        return

    contexto = _build_unifamiliar_context(calc, rule)
    render_relatorio_unifamiliar(contexto)
    # Mantidas por blindagem / compatibilidade de hooks
    render_zone_description_section(calc)
    render_quadro_tecnico()
    render_dicas_valiosas()
    render_figuras_anexo_v(rule)
