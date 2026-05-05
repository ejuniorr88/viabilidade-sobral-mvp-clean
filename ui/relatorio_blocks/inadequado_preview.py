from __future__ import annotations

from typing import Any, Dict

import math
import streamlit as st

from core.zone_descriptions import fetch_zone_description
from ui.relatorio_blocks.unifamiliar_items import UNIFAMILIAR_ITEM_RENDERERS
from ui.relatorio_blocks.multifamiliar_items import common as mf_common
from ui.relatorio_blocks.credit_preserved_notice import render_credit_preserved_notice

DEBUG_SESSION_KEY = "_debug_inadequado_flow"


def _build_debug_snapshot(calc: Dict[str, Any], ctx: Dict[str, Any] | None = None) -> Dict[str, Any]:
    ctx = ctx or {}
    return {
        "project_mode": calc.get("project_mode"),
        "use_type_code": calc.get("use_type_code"),
        "zone": calc.get("zone"),
        "zone_sigla": calc.get("zone_sigla"),
        "zone_lookup": calc.get("zone_lookup"),
        "subzone_code": calc.get("subzone_code"),
        "zone_label_raw": calc.get("zone_label_raw"),
        "via_nome": calc.get("via_nome") or calc.get("street_name"),
        "via_tipo": calc.get("via_tipo") or calc.get("street_type"),
        "has_rule": bool(calc.get("rule")),
        "rule_zone_sigla": (calc.get("rule") or {}).get("zone_sigla") if isinstance(calc.get("rule"), dict) else None,
        "rule_subzone_code": (calc.get("rule") or {}).get("subzone_code") if isinstance(calc.get("rule"), dict) else None,
        "calc_err": calc.get("err"),
        "ctx_status_curto": ctx.get("status_curto"),
        "ctx_icon": ctx.get("icon"),
        "ctx_zone_class": ctx.get("zone_class"),
        "ctx_via_class": ctx.get("via_class"),
        "ctx_via_norm": ctx.get("via_norm"),
        "ctx_explicacao": ctx.get("explicacao"),
        "ctx_tipo_lote": ctx.get("tipo_lote"),
        "ctx_zone_title": ctx.get("zone_title"),
        "ctx_adequabilidade_debug": ctx.get("adeq_dbg"),
        "session_lot_front_m": st.session_state.get("lot_front_m"),
        "session_lot_depth_m": st.session_state.get("lot_depth_m"),
        "session_lot_is_corner": st.session_state.get("lot_is_corner"),
        "session_lot_is_irregular": st.session_state.get("lot_is_irregular"),
        "session_built_ground_m2": st.session_state.get("built_ground_m2"),
        "session_built_ground_input_m2": st.session_state.get("built_ground_input_m2"),
        "session_free_calc_done": st.session_state.get("free_calc_done"),
        "session_report_unlocked": st.session_state.get("report_unlocked"),
    }


def _store_debug_snapshot(calc: Dict[str, Any], ctx: Dict[str, Any] | None = None, stage: str = "") -> Dict[str, Any]:
    payload = _build_debug_snapshot(calc, ctx)
    payload["stage"] = stage
    st.session_state[DEBUG_SESSION_KEY] = payload
    return payload


def render_debug_snapshot(snapshot: Dict[str, Any] | None = None, title: str = "Debug provisório — fluxo inadequado") -> None:
    payload = snapshot or st.session_state.get(DEBUG_SESSION_KEY) or {}
    with st.expander(title):
        st.json(payload)


def _safe_float(v: Any) -> float | None:
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None


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


def _zone_title(zone_sigla: str, desc: dict | None) -> str:
    sigla = str(zone_sigla or "").strip()
    title = str((desc or {}).get("title") or "").strip()
    if not title:
        return sigla or "Zona não identificada"
    title_upper = title.upper()
    sigla_upper = sigla.upper()
    if not sigla:
        return title
    if title_upper == sigla_upper:
        return sigla
    if title_upper.startswith(sigla_upper + " —") or title_upper.startswith(sigla_upper + " -"):
        return title
    return f"{sigla} — {title}"


def _use_label(uso: str) -> str:
    code = str(uso or "").upper().strip()
    mapping = {
        "RES_UNI": "residência unifamiliar",
        "RES_MULTI_R21": "residência multifamiliar",
        "RES_MULTI_R22": "residência multifamiliar",
        "RES_MULTI_R3": "residência multifamiliar",
    }
    return mapping.get(code, code or "uso informado")


def _fetch_adequabilidade_unifamiliar(zone_sigla: str, via_tipo_texto: str | None):
    attempts = []
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


def _is_multifamiliar(calc: Dict[str, Any]) -> bool:
    use_type_code = str(calc.get("use_type_code") or "").upper()
    project_mode = str(calc.get("project_mode") or "").upper()
    return use_type_code.startswith("RES_MULTI_") and project_mode == "GUIA_FASE_1"


def _build_unifamiliar_ctx(calc: Dict[str, Any]) -> Dict[str, Any]:
    rule = calc.get("rule") or {}
    zone = calc.get("zone") or calc.get("zone_sigla") or "—"
    via = calc.get("via_nome") or calc.get("street_name") or "—"
    via_tipo = calc.get("via_tipo") or calc.get("street_type") or "—"
    uso = calc.get("use_type_code") or "RES_UNI"
    uso_label = _use_label(uso)

    A = float(calc.get("lot_area_m2") or 0.0)
    W = float(st.session_state.get("lot_front_m") or 0.0)
    D = float(st.session_state.get("lot_depth_m") or 0.0)
    is_corner = bool(st.session_state.get("lot_is_corner") or False)
    tipo_lote = "Esquina" if is_corner else "Meio de quadra"

    to_max = _to_pct(rule, "to_max_pct", "to_max")
    tp_min = _to_pct(rule, "tp_min_pct", "tp_min")
    ia_max = rule.get("ia_max")
    ia_min = rule.get("ia_min")
    rec_fr = float(rule.get("recuo_frontal_m") or 0.0)
    rec_lat = float(rule.get("recuo_lateral_m") or 0.0)
    rec_fun = float(rule.get("recuo_fundos_m") or 0.0)
    gabarito_m = _safe_float(rule.get("gabarito_m"))

    A_to = A * (to_max / 100.0) if (A and to_max is not None) else None
    A_perm_min = A * (tp_min / 100.0) if (A and tp_min is not None) else None
    A_total = A * float(ia_max) if (A and ia_max is not None) else None

    built_ground = _safe_float(
        st.session_state.get("built_ground_m2")
        or calc.get("built_ground_m2")
        or st.session_state.get("built_ground_input_m2")
        or calc.get("built_ground_input_m2")
    )

    W_util = W - 2 * rec_lat
    D_util = D - rec_fr - rec_fun
    A_recuos = (W_util * D_util) if (W_util > 0 and D_util > 0) else None
    A_op1_max = min(A_to, A_recuos) if (A_to is not None and A_recuos is not None) else None

    A_fundo = (W * (D - rec_fun)) if (W > 0 and D > rec_fun) else None
    if A_to is not None and A_fundo is not None:
        A_op2_max = min(A_to, A_fundo)
    elif A_to is not None:
        A_op2_max = A_to
    else:
        A_op2_max = None

    def _tp_scenario(a_terreo: float | None):
        if a_terreo is None or A_perm_min is None:
            return None
        a_rest = A - a_terreo
        a_imperm_max = a_rest - A_perm_min
        return a_rest, a_imperm_max

    tp1 = _tp_scenario(A_op1_max)
    tp2 = _tp_scenario(A_op2_max)

    A_teto_projeto = A_op2_max or A_op1_max or A_to
    area_pedida = built_ground if (built_ground is not None and built_ground > 0) else None
    A_considerada = None
    if built_ground is not None and built_ground > 0:
        A_considerada = min(built_ground, A_teto_projeto) if A_teto_projeto is not None else built_ground
    excedeu_area = bool(area_pedida is not None and A_considerada is not None and area_pedida > A_considerada)

    to_projeto_pct = ((A_considerada / A) * 100.0) if (A_considerada is not None and A > 0) else None
    A_livre = (A - A_considerada) if (A_considerada is not None and A > 0) else None
    A_impermeavel_possivel = (A_livre - A_perm_min) if (A_livre is not None and A_perm_min is not None) else None
    A_ia_saldo = (A_total - A_considerada) if (A_total is not None and A_considerada is not None) else None

    zone_sigla = calc.get("zone_sigla") or calc.get("zone_lookup") or zone or rule.get("zone_sigla") or ""
    subzone_code = calc.get("subzone_code") or rule.get("subzone_code") or "PADRAO"
    zone_label = calc.get("zone_label_raw") or calc.get("zone") or zone_sigla
    try:
        desc = fetch_zone_description(str(zone_sigla), str(subzone_code), str(zone_label))
    except Exception:
        desc = None
    zone_title = _zone_title(str(zone_sigla or zone), desc)

    zone_class, via_class, adeq_dbg = _fetch_adequabilidade_unifamiliar(
        zone_sigla=str(zone_sigla or zone or ""),
        via_tipo_texto=via_tipo,
    )
    via_norm = mf_common._via_tipo_norm(via_tipo)
    icon, status_curto, explicacao = mf_common._summarize_adequabilidade(
        zone_class=zone_class,
        via_norm=via_norm,
        via_class=via_class,
    )

    recuos_resumo = f"Frontal: {mf_common._fmt_num(rec_fr)} m | Laterais: {mf_common._fmt_num(rec_lat)} m | Fundos: {mf_common._fmt_num(rec_fun)} m"
    ia_min_texto = mf_common._fmt_num(ia_min) if ia_min is not None else "não informado"
    pav_est = None
    if gabarito_m is not None and gabarito_m > 0:
        pav_est = max(1, int(math.floor(gabarito_m / 3.0)))

    return {
        "calc": calc,
        "rule": rule,
        "zone": zone,
        "via": via,
        "via_tipo": via_tipo,
        "uso": uso,
        "uso_label": uso_label,
        "A": A,
        "W": W,
        "D": D,
        "is_corner": is_corner,
        "tipo_lote": tipo_lote,
        "to_max": to_max,
        "tp_min": tp_min,
        "ia_max": ia_max,
        "ia_min": ia_min,
        "rec_fr": rec_fr,
        "rec_lat": rec_lat,
        "rec_fun": rec_fun,
        "gabarito_m": gabarito_m,
        "A_to": A_to,
        "A_perm_min": A_perm_min,
        "A_total": A_total,
        "built_ground": built_ground,
        "W_util": W_util,
        "D_util": D_util,
        "A_recuos": A_recuos,
        "A_op1_max": A_op1_max,
        "A_fundo": A_fundo,
        "A_op2_max": A_op2_max,
        "tp1": tp1,
        "tp2": tp2,
        "A_teto_projeto": A_teto_projeto,
        "area_pedida": area_pedida,
        "A_considerada": A_considerada,
        "excedeu_area": excedeu_area,
        "to_projeto_pct": to_projeto_pct,
        "A_livre": A_livre,
        "A_impermeavel_possivel": A_impermeavel_possivel,
        "A_ia_saldo": A_ia_saldo,
        "zone_sigla": zone_sigla,
        "subzone_code": subzone_code,
        "zone_label": zone_label,
        "desc": desc,
        "zone_title": zone_title,
        "zone_class": zone_class,
        "via_class": via_class,
        "adeq_dbg": adeq_dbg,
        "via_norm": via_norm,
        "icon": icon,
        "status_curto": status_curto,
        "explicacao": explicacao,
        "recuos_resumo": recuos_resumo,
        "ia_min_texto": ia_min_texto,
        "pav_est": pav_est,
        "render_quadro_tecnico": lambda *_args, **_kwargs: None,
        "render_figuras_anexo_v": lambda *_args, **_kwargs: None,
        "_mf_sigla_nome": mf_common._sigla_nome,
    }


def _build_multifamiliar_ctx(calc: Dict[str, Any]) -> Dict[str, Any]:
    from ui.relatorio_blocks.multifamiliar_guia import _fetch_adequabilidade as _mf_fetch_adequabilidade

    mf_common.st = st
    return mf_common.build_context(
        calc=calc,
        rule=calc.get("rule"),
        fetch_adequabilidade_fn=_mf_fetch_adequabilidade,
    )


def should_block_report(calc: Dict[str, Any]) -> bool:
    try:
        ctx = _build_multifamiliar_ctx(calc) if _is_multifamiliar(calc) else _build_unifamiliar_ctx(calc)
        _store_debug_snapshot(calc, ctx, stage="should_block_report")
        return str(ctx.get("status_curto") or "").strip().upper() == "NÃO PERMITE"
    except Exception as e:
        st.session_state[DEBUG_SESSION_KEY] = {
            "stage": "should_block_report_exception",
            "error": str(e),
            "project_mode": calc.get("project_mode"),
            "use_type_code": calc.get("use_type_code"),
            "zone": calc.get("zone"),
            "zone_sigla": calc.get("zone_sigla"),
            "subzone_code": calc.get("subzone_code"),
            "via_tipo": calc.get("via_tipo") or calc.get("street_type"),
        }
        return False


def render_block_message() -> None:
    st.markdown("---\n### 🚫 Situação do estudo")
    st.error("A análise de adequabilidade resultou em **NÃO PERMITE** para a condição atual deste terreno.")
    st.markdown(
        "Por isso, o relatório completo não será continuado, já que não há viabilidade urbanística para este caso na forma analisada."
    )
    render_credit_preserved_notice()


def render_inadequado_preview(calc: Dict[str, Any]) -> None:
    if _is_multifamiliar(calc):
        from ui.relatorio_blocks.multifamiliar_items import (
            render_item_00_intro as _mf_render_item_00_intro,
            render_item_01 as _mf_render_item_01,
            render_item_02 as _mf_render_item_02,
            render_item_03 as _mf_render_item_03,
        )

        ctx = _build_multifamiliar_ctx(calc)
        render_debug_snapshot(_store_debug_snapshot(calc, ctx, stage="render_inadequado_preview_multifamiliar"))
        _mf_render_item_00_intro(ctx)
        st.markdown("---\n### 📍 1️⃣ Onde está localizado o terreno?")
        _mf_render_item_01(ctx)
        st.markdown("---\n### ✅ 2️⃣ O uso residencial multifamiliar é viável neste terreno?")
        _mf_render_item_02(ctx)
        st.markdown("---\n### 📘 3️⃣ Como funciona a leitura da adequabilidade no multifamiliar?")
        _mf_render_item_03(ctx)
        render_block_message()
        return

    ctx = _build_unifamiliar_ctx(calc)
    render_debug_snapshot(_store_debug_snapshot(calc, ctx, stage="render_inadequado_preview_unifamiliar"))
    st.markdown("## 🏡 RELATÓRIO URBANÍSTICO")
    st.markdown(
        "Este relatório mostra, de forma simples, o que pode ou não pode ser feito no terreno informado, "
        "com base na zona, na via e nas regras urbanísticas do município.\n\n"
        "A ideia aqui é facilitar a leitura: primeiro mostramos onde o terreno está, depois se o uso é viável, "
        "e em seguida explicamos os principais limites do lote, como ocupação, área livre, altura, vagas, ambientes mínimos e calçada.\n\n"
        "**Importante:** este relatório é uma análise inicial. A aprovação final depende da conferência completa no licenciamento."
    )
    headings = {
        "item_01": "---\n### 📍 1️⃣ Onde está localizado o terreno?",
        "item_02": "---\n### ✅ 2️⃣ O uso residencial unifamiliar é viável neste terreno?",
        "item_03": "---\n### 📘 3️⃣ Como funciona a leitura da adequabilidade no unifamiliar?",
    }
    for item_key in ("item_01", "item_02", "item_03"):
        st.markdown(headings[item_key])
        UNIFAMILIAR_ITEM_RENDERERS[item_key](ctx)
    render_block_message()
