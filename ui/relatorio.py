from __future__ import annotations

from typing import Any, Dict

from .relatorio_blocks.credit_preserved_notice import render_credit_preserved_notice

import math
import streamlit as st

from .relatorio_blocks import (
    render_quadro_tecnico,
    render_dicas_valiosas,
    render_figuras_anexo_v,
    render_multifamiliar_guia,
)
from .relatorio_blocks.multifamiliar_guia import (
    _fetch_adequabilidade as _mf_fetch_adequabilidade,
    _sigla_nome as _mf_sigla_nome,
    _summarize_adequabilidade as _mf_summarize_adequabilidade,
    _via_tipo_norm as _mf_via_tipo_norm,
)
from core.zone_descriptions import fetch_zone_description
from urban_rules.zone_profiles import apply_zone_result_policy, zone_context_warnings
from .relatorio_blocks.unifamiliar_items import UNIFAMILIAR_ITEM_RENDERERS


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



def _is_zeia_zone_for_report(zona: Any) -> bool:
    z = str(zona or "").strip().upper()
    z_key = z.replace("-", "").replace("/", "").replace(" ", "")
    return z_key in {"ZEIAAPP", "ZEIA1", "ZEIA2", "ZEIA3"}


def _append_zeia_ambiental_observacao(*, zona: Any, status_curto: str, explicacao: str) -> str:
    if not (_is_zeia_zone_for_report(zona) and str(status_curto or "").strip().upper() == "PERMITE PELA VIA"):
        return explicacao
    observacao = (
        "\n\n**Observação ambiental e documental:** como o terreno está em área de interesse ambiental, "
        "a viabilidade final não dispensa análise do órgão municipal competente, verificação das restrições ambientais aplicáveis, "
        "atendimento aos parâmetros urbanísticos da zona e comprovação da regularidade documental do imóvel, "
        "como matrícula, escritura, registro ou outro documento hábil exigido no licenciamento."
    )
    if observacao.strip() in str(explicacao or ""):
        return explicacao
    return f"{explicacao}{observacao}"

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


def _md_table(rows: list[tuple[str, str]]) -> str:
    out = ["| Tipo de Piso | Percentual considerado permeável |", "|---|---:|"]
    for a, b in rows:
        out.append(f"| {a} | {b} |")
    return "\n".join(out)


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
    final_dbg["attempts"] = [{"use_type_code": u, "zone_class": z, "via_class": v} for u,z,v,_ in attempts]
    return None, None, final_dbg
def render_zone_description_section(calc: Dict[str, Any]) -> None:
    # Compatibilidade mantida: o app principal chama esta função antes do relatório.
    # Para evitar repetição do bloco da zona, a renderização visível agora acontece
    # dentro do próprio relatório urbanístico.
    return


def _build_unifamiliar_preview_context(calc: Dict[str, Any]) -> Dict[str, Any] | None:
    if not isinstance(calc, dict) or not calc.get("ok"):
        return None

    rule = calc.get("rule") or {}
    zone = calc.get("zone") or calc.get("zone_sigla") or "—"
    via = calc.get("via_nome") or calc.get("street_name") or "—"
    via_tipo = calc.get("via_tipo") or calc.get("street_type") or "—"
    uso = calc.get("use_type_code") or "RES_UNI"
    uso_label = _use_label(uso)

    A = float(calc.get("lot_area_m2") or 0.0)
    is_irregular = bool(
        st.session_state.get("lot_is_irregular")
        or calc.get("lot_irregular")
        or calc.get("lot_is_irregular")
    )
    if is_irregular:
        W = 0.0
        D = 0.0
        is_corner = False
        tipo_lote = "Terreno irregular"
    else:
        W = float(st.session_state.get("lot_front_m") or calc.get("lot_front_m") or 0.0)
        D = float(st.session_state.get("lot_depth_m") or calc.get("lot_depth_m") or 0.0)
        is_corner = bool(st.session_state.get("lot_is_corner") or calc.get("lot_is_corner") or False)
        tipo_lote = "Esquina" if is_corner else "Meio de quadra"

    to_max = _to_pct(rule, "to_max_pct", "to_max")
    tp_min = _to_pct(rule, "tp_min_pct", "tp_min")
    ia_max = rule.get("ia_max")
    ia_min = rule.get("ia_min")
    rec_fr = float(rule.get("recuo_frontal_m") or 0.0)
    rec_lat = float(rule.get("recuo_lateral_m") or 0.0)
    rec_fun = float(rule.get("recuo_fundos_m") or 0.0)
    gabarito_m = _safe_float(rule.get("gabarito_m"))
    area_min_lote = _safe_float(rule.get("area_min_lote_m2") or rule.get("area_lote_min_m2") or rule.get("lote_min_area_m2"))
    area_max_lote = _safe_float(rule.get("area_max_lote_m2") or rule.get("lote_max_area_m2"))
    
    if is_corner:
        testada_min_lote = _safe_float(rule.get("testada_min_esquina_m") or rule.get("testada_min_m") or rule.get("testada_min_meio_m"))
    else:
        testada_min_lote = _safe_float(rule.get("testada_min_meio_m") or rule.get("testada_min_m") or rule.get("testada_min_esquina_m"))
    testada_max_lote = _safe_float(rule.get("testada_max_m"))

    A_to = A * (to_max / 100.0) if (A and to_max is not None) else None
    A_perm_min = A * (tp_min / 100.0) if (A and tp_min is not None) else None
    A_total = A * float(ia_max) if (A and ia_max is not None) else None

    built_ground = _safe_float(
        st.session_state.get("built_ground_m2")
        or calc.get("built_ground_m2")
        or st.session_state.get("built_ground_input_m2")
        or calc.get("built_ground_input_m2")
    )

    if is_irregular:
        # Terreno irregular não possui testada/profundidade retangulares confiáveis.
        # Portanto, não calculamos largura útil, profundidade útil nem área física por recuos.
        W_util = None
        D_util = None
        A_recuos = None
        A_op1_max = None
        A_fundo = None
        A_op2_max = A_to
    else:
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
    via_norm = _mf_via_tipo_norm(via_tipo)
    icon, status_curto, explicacao = _mf_summarize_adequabilidade(
        zone_class=zone_class,
        via_norm=via_norm,
        via_class=via_class,
    )
    policy = apply_zone_result_policy(
        zona=zone_sigla or zone,
        subzona=subzone_code,
        via_norm=via_norm,
        via_class=via_class,
        zone_class=zone_class,
        status=status_curto,
        icon=icon,
        explanation=explicacao,
        use_type_code=uso,
    )
    icon, status_curto, explicacao = policy.icon, policy.status, policy.explanation

    recuos_resumo = f"Frontal: {_fmt_num(rec_fr)} m | Laterais: {_fmt_num(rec_lat)} m | Fundos: {_fmt_num(rec_fun)} m"
    ia_min_texto = _fmt_num(ia_min) if ia_min is not None else "não informado"
    is_zeip9_unif = str(subzone_code or "").strip().upper().replace("-", "_") in ("ZEIP_9", "ZEIP9")

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
        "is_irregular": is_irregular,
        "tipo_lote": tipo_lote,
        "to_max": to_max,
        "tp_min": tp_min,
        "ia_max": ia_max,
        "ia_min": ia_min,
        "rec_fr": rec_fr,
        "rec_lat": rec_lat,
        "rec_fun": rec_fun,
        "gabarito_m": gabarito_m,
        "area_min_lote": area_min_lote,
        "area_max_lote": area_max_lote,
        "testada_min_lote": testada_min_lote,
        "testada_max_lote": testada_max_lote,
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
        "is_zeip9": is_zeip9_unif,
        "lot_area_f": A,
        "lot_front": W,
        "area_min": area_min_lote,
        "area_max": area_max_lote,
        "testada_min": testada_min_lote,
        "testada_max": testada_max_lote,
        "render_quadro_tecnico": render_quadro_tecnico,
        "render_figuras_anexo_v": render_figuras_anexo_v,
        "_mf_sigla_nome": _mf_sigla_nome,
    }


def should_block_unifamiliar_preview(calc: Dict[str, Any]) -> bool:
    if not isinstance(calc, dict):
        return False
    if not calc.get("ok") or not calc.get("rule") or not (calc.get("zone") or calc.get("zone_sigla")) or calc.get("err"):
        return False
    if str(calc.get("use_type_code") or "").startswith("RES_MULTI_") and calc.get("project_mode") == "GUIA_FASE_1":
        return False
    ctx = _build_unifamiliar_preview_context(calc)
    return bool(ctx and str(ctx.get("status_curto") or "").strip().upper() == "NÃO PERMITE")


def render_unifamiliar_inadequado_preview(calc: Dict[str, Any]) -> None:
    ctx = _build_unifamiliar_preview_context(calc)
    if not ctx:
        st.info("Não foi possível montar o preview do relatório para este caso.")
        return

    st.subheader("6) Relatório Urbanístico")
    st.markdown("## 🏡 RELATÓRIO URBANÍSTICO")
    st.markdown(
        "Este relatório mostra, de forma simples, o que pode ou não pode ser feito no terreno informado, "
        "com base na zona, na via e nas regras urbanísticas do município.\n\n"
        "A ideia aqui é facilitar a leitura: primeiro mostramos onde o terreno está, depois se o uso é viável.\n\n"
        "**Importante:** este relatório é uma análise inicial. A aprovação final depende da conferência completa no licenciamento."
    )

    item_headings = {
        "item_01": "---\n### 📍 1️⃣ Onde está localizado o terreno?",
        "item_02": "---\n### ✅ 2️⃣ O uso residencial unifamiliar é viável neste terreno?",
    }
    for item_key in ["item_01", "item_02"]:
        st.markdown(item_headings[item_key])
        UNIFAMILIAR_ITEM_RENDERERS[item_key](ctx)

    st.markdown("---\n### ⚠️ Situação do estudo")
    st.warning("A análise de adequabilidade resultou em **NÃO PERMITE** para a condição atual deste terreno.")
    st.markdown(
        "Por isso, o relatório completo não será continuado, já que não há viabilidade urbanística para este caso na forma analisada."
    )
    render_credit_preserved_notice()


def render_relatorio_section(calc: Dict[str, Any]) -> None:
    is_irregular = bool(st.session_state.get("lot_is_irregular", False))

    st.subheader("6) Relatório Urbanístico")

    if not isinstance(calc, dict) or not calc.get("ok"):
        st.info("Clique em **Gerar consulta aos índices urbanísticos** para gerar o relatório.")
        return

    rule = calc.get("rule") or {}
    zone = calc.get("zone") or calc.get("zone_sigla") or "—"
    via = calc.get("via_nome") or calc.get("street_name") or "—"
    via_tipo = calc.get("via_tipo") or calc.get("street_type") or "—"
    uso = calc.get("use_type_code") or "RES_UNI"
    uso_label = _use_label(uso)
    is_irregular = bool(
        st.session_state.get("lot_is_irregular")
        or calc.get("lot_irregular")
        or calc.get("lot_is_irregular")
    )

    if str(uso).startswith("RES_MULTI_") and calc.get("project_mode") == "GUIA_FASE_1":
        render_multifamiliar_guia(calc=calc, rule=rule, is_irregular=is_irregular)
        return

    A = float(calc.get("lot_area_m2") or 0.0)
    if is_irregular:
        W = 0.0
        D = 0.0
        is_corner = False
        tipo_lote = "Terreno irregular"
    else:
        W = float(st.session_state.get("lot_front_m") or calc.get("lot_front_m") or 0.0)
        D = float(st.session_state.get("lot_depth_m") or calc.get("lot_depth_m") or 0.0)
        is_corner = bool(st.session_state.get("lot_is_corner") or calc.get("lot_is_corner") or False)
        tipo_lote = "Esquina" if is_corner else "Meio de quadra"

    to_max = _to_pct(rule, "to_max_pct", "to_max")
    tp_min = _to_pct(rule, "tp_min_pct", "tp_min")
    ia_max = rule.get("ia_max")
    ia_min = rule.get("ia_min")
    rec_fr = float(rule.get("recuo_frontal_m") or 0.0)
    rec_lat = float(rule.get("recuo_lateral_m") or 0.0)
    rec_fun = float(rule.get("recuo_fundos_m") or 0.0)
    gabarito_m = _safe_float(rule.get("gabarito_m"))
    area_min_lote = _safe_float(rule.get("area_min_lote_m2") or rule.get("area_lote_min_m2") or rule.get("lote_min_area_m2"))
    area_max_lote = _safe_float(rule.get("area_max_lote_m2") or rule.get("lote_max_area_m2"))
    
    if is_corner:
        testada_min_lote = _safe_float(rule.get("testada_min_esquina_m") or rule.get("testada_min_m") or rule.get("testada_min_meio_m"))
    else:
        testada_min_lote = _safe_float(rule.get("testada_min_meio_m") or rule.get("testada_min_m") or rule.get("testada_min_esquina_m"))
    testada_max_lote = _safe_float(rule.get("testada_max_m"))

    A_to = A * (to_max / 100.0) if (A and to_max is not None) else None
    A_perm_min = A * (tp_min / 100.0) if (A and tp_min is not None) else None
    A_total = A * float(ia_max) if (A and ia_max is not None) else None

    built_ground = _safe_float(
        st.session_state.get("built_ground_m2")
        or calc.get("built_ground_m2")
        or st.session_state.get("built_ground_input_m2")
        or calc.get("built_ground_input_m2")
    )

    if is_irregular:
        # Terreno irregular não possui testada/profundidade retangulares confiáveis.
        # Portanto, não calculamos largura útil, profundidade útil nem área física por recuos.
        W_util = None
        D_util = None
        A_recuos = None
        A_op1_max = None
        A_fundo = None
        A_op2_max = A_to
    else:
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
    via_norm = _mf_via_tipo_norm(via_tipo)
    icon, status_curto, explicacao = _mf_summarize_adequabilidade(
        zone_class=zone_class,
        via_norm=via_norm,
        via_class=via_class,
    )
    policy = apply_zone_result_policy(
        zona=zone_sigla or zone,
        subzona=subzone_code,
        via_norm=via_norm,
        via_class=via_class,
        zone_class=zone_class,
        status=status_curto,
        icon=icon,
        explanation=explicacao,
        use_type_code=uso,
    )
    icon, status_curto, explicacao = policy.icon, policy.status, policy.explanation

    recuos_resumo = f"Frontal: {_fmt_num(rec_fr)} m | Laterais: {_fmt_num(rec_lat)} m | Fundos: {_fmt_num(rec_fun)} m"
    ia_min_texto = _fmt_num(ia_min) if ia_min is not None else "não informado"
    is_zeip9_unif = str(subzone_code or "").strip().upper().replace("-", "_") in ("ZEIP_9", "ZEIP9")

    pav_est = None
    if gabarito_m is not None and gabarito_m > 0:
        pav_est = max(1, int(math.floor(gabarito_m / 3.0)))

    st.markdown("## 🏡 RELATÓRIO URBANÍSTICO")
    st.markdown(
        "Este relatório mostra, de forma simples, o que pode ou não pode ser feito no terreno informado, "
        "com base na zona, na via e nas regras urbanísticas do município.\n\n"
        "A ideia aqui é facilitar a leitura: primeiro mostramos onde o terreno está, depois se o uso é viável, "
        "e em seguida explicamos os principais limites do lote, como ocupação, área livre, altura, vagas, ambientes mínimos e calçada.\n\n"
        "**Importante:** este relatório é uma análise inicial. A aprovação final depende da conferência completa no licenciamento."
    )

    item_headings = {
        "item_01": "---\n### 📍 1️⃣ Onde está localizado o terreno?",
        "item_02": "---\n### ✅ 2️⃣ O uso residencial unifamiliar é viável neste terreno?",
        "item_03": "---\n### 📘 3️⃣ Como funciona a leitura da adequabilidade no unifamiliar?",
        "item_04": "---\n### 🧭 4️⃣ O que essa zona permite neste terreno?",
        "item_05": "---\n### 📏 5️⃣ Regras principais para este terreno",
        "item_06": "---\n### 📐 6️⃣ Quanto posso ocupar no térreo?",
        "item_07": "---\n### 🌿 7️⃣ Quanto preciso deixar livre?",
        "item_08": "---\n### 🧱 8️⃣ Tipos de piso: o que conta como permeável?",
        "item_09": "---\n### 🏢 9️⃣ Posso construir mais andares?",
        "item_10": "---\n### 🚗 1️⃣0️⃣ Preciso de vagas de estacionamento?",
        "item_11": "---\n### 📋 1️⃣1️⃣ Quais medidas mínimas os ambientes precisam ter?",
        "item_12": "---\n### 🚶 1️⃣2️⃣ O que preciso saber sobre a calçada?",
        "item_13": "---\n### 💡 1️⃣3️⃣ Dicas valiosas",
        "item_14": "---\n### 📌 1️⃣4️⃣ Resumo rápido final",
        "item_15": "---\n### 🏛️ 1️⃣5️⃣ O que acontece depois desta etapa?",
        "item_16": "---\n### ✅ 1️⃣6️⃣ Fechamento final",
    }

    ctx = {
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
        "is_irregular": is_irregular,
        "tipo_lote": tipo_lote,
        "to_max": to_max,
        "tp_min": tp_min,
        "ia_max": ia_max,
        "ia_min": ia_min,
        "rec_fr": rec_fr,
        "rec_lat": rec_lat,
        "rec_fun": rec_fun,
        "gabarito_m": gabarito_m,
        "area_min_lote": area_min_lote,
        "area_max_lote": area_max_lote,
        "testada_min_lote": testada_min_lote,
        "testada_max_lote": testada_max_lote,
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
        "is_zeip9": is_zeip9_unif,
        "lot_area_f": A,
        "lot_front": W,
        "area_min": area_min_lote,
        "area_max": area_max_lote,
        "testada_min": testada_min_lote,
        "testada_max": testada_max_lote,
        "render_quadro_tecnico": render_quadro_tecnico,
        "render_figuras_anexo_v": render_figuras_anexo_v,
        "_mf_sigla_nome": _mf_sigla_nome,
    }
    ctx["zone_warnings"] = zone_context_warnings(ctx)

    for item_key in [
        "item_01", "item_02", "item_03", "item_04", "item_05", "item_06", "item_07", "item_08",
        "item_09", "item_10", "item_11", "item_12", "item_13", "item_14", "item_15", "item_16",
    ]:
        st.markdown(item_headings[item_key])
        UNIFAMILIAR_ITEM_RENDERERS[item_key](ctx)

