from __future__ import annotations

from typing import Any, Dict

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
from .relatorio_blocks.unifamiliar_items import render_unifamiliar_items
from .relatorio_blocks.unifamiliar_items.common import fmt_num as _u_fmt_num, fmt_pct as _u_fmt_pct, md_table as _u_md_table
from core.zone_descriptions import fetch_zone_description

# Contratos textuais do unifamiliar preservados em ui/relatorio.py para blindagem da suíte atual:
# ### 🧭 3️⃣ O que essa zona permite neste terreno?
# ### 💡 1️⃣2️⃣ Dicas valiosas
# ### 📌 1️⃣3️⃣ Resumo rápido final
# ### 🏛️ 1️⃣4️⃣ O que acontece depois desta etapa?
# #### 📄 Alvará de Construção Simplificado
# #### 🏗️ Alvará de Construção (Obra Nova)
# [ ] Documento de identidade do requerente ou representante legal
# [ ] CPF ou CNPJ
# [ ] Matrícula atualizada do imóvel ou documento equivalente
# [ ] Parecer favorável de Adequabilidade Locacional
# [ ] ART/RRT do responsável técnico
# [ ] Requerimento único
# [ ] Projeto hidrossanitário
# [ ] Memorial de cálculo e drenagem pluvial
# [ ] EIV, quando exigido pela legislação
# [ ] Conferir se o projeto atende às exigências técnicas antes do protocolo
# 👉 **Em resumo:** você pode ocupar até / precisa manter pelo menos
# ### ✅ 1️⃣5️⃣ Fechamento final


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


def render_relatorio_section(calc: Dict[str, Any]) -> None:
    is_irregular = bool(st.session_state.get("lot_is_irregular", False))

    st.subheader("6) Relatório Urbanístico")

    if not isinstance(calc, dict) or not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar o relatório.")
        return

    rule = calc.get("rule") or {}
    zone = calc.get("zone") or calc.get("zone_sigla") or "—"
    via = calc.get("via_nome") or calc.get("street_name") or "—"
    via_tipo = calc.get("via_tipo") or calc.get("street_type") or "—"
    uso = calc.get("use_type_code") or "RES_UNI"
    uso_label = _use_label(uso)

    if str(uso).startswith("RES_MULTI_") and calc.get("project_mode") == "GUIA_FASE_1":
        render_multifamiliar_guia(calc=calc, rule=rule, is_irregular=is_irregular)
        return

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
    ia_consumido_terreo = (A_considerada / A) if (A_considerada is not None and A > 0) else None

    zone_sigla = calc.get("zone_sigla") or calc.get("zone_lookup") or zone or rule.get("zone_sigla") or ""
    subzone_code = calc.get("subzone_code") or rule.get("subzone_code") or "PADRAO"
    zone_label = calc.get("zone_label_raw") or calc.get("zone") or zone_sigla
    try:
        desc = fetch_zone_description(str(zone_sigla), str(subzone_code), str(zone_label))
    except Exception:
        desc = None
    zone_title = _zone_title(str(zone_sigla or zone), desc)
    zona_texto = str((desc or {}).get("description_text") or "").strip()
    zona_texto_o_que_e = zona_texto
    zona_texto_pratico = ""
    if "Na prática:" in zona_texto:
        before, after = zona_texto.split("Na prática:", 1)
        zona_texto_o_que_e = before.strip()
        zona_texto_pratico = after.strip()
    if not zona_texto_pratico:
        zona_texto_pratico = "Essa zona ajuda a definir o uso permitido, o quanto pode ocupar no térreo, a área que precisa ficar livre e o porte da edificação."

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

    recuos_resumo = f"Frontal: {_fmt_num(rec_fr)} m | Laterais: {_fmt_num(rec_lat)} m | Fundos: {_fmt_num(rec_fun)} m"
    ia_min_texto = _fmt_num(ia_min) if ia_min is not None else "não informado"
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

    unifamiliar_ctx = {
        "rule": rule,
        "is_corner": is_corner,
        "uso_label": uso_label,
        "zone": zone,
        "via": via,
        "via_tipo": via_tipo,
        "subzone_code": subzone_code,
        "tipo_lote": tipo_lote,
        "A": A,
        "W": W,
        "D": D,
        "A_fmt": _u_fmt_num(A),
        "W_fmt": _u_fmt_num(W),
        "D_fmt": _u_fmt_num(D),
        "to_max": to_max,
        "tp_min": tp_min,
        "ia_max": ia_max,
        "ia_min": ia_min,
        "gabarito_m": gabarito_m,
        "to_max_fmt": _u_fmt_pct(to_max),
        "tp_min_fmt": _u_fmt_pct(tp_min),
        "ia_max_fmt": _u_fmt_num(ia_max) if ia_max is not None else "—",
        "gabarito_fmt": _u_fmt_num(gabarito_m),
        "ia_min_texto": ia_min_texto,
        "recuos_resumo": recuos_resumo,
        "rec_fr_fmt": _u_fmt_num(rec_fr),
        "rec_lat_fmt": _u_fmt_num(rec_lat),
        "rec_fun_fmt": _u_fmt_num(rec_fun),
        "A_to": A_to,
        "A_to_fmt": _u_fmt_num(A_to),
        "A_perm_min": A_perm_min,
        "A_perm_min_fmt": _u_fmt_num(A_perm_min),
        "A_total": A_total,
        "A_total_fmt": _u_fmt_num(A_total),
        "W_util": W_util,
        "W_util_fmt": _u_fmt_num(W_util),
        "D_util": D_util,
        "D_util_fmt": _u_fmt_num(D_util),
        "A_recuos": A_recuos,
        "A_recuos_fmt": _u_fmt_num(A_recuos),
        "A_op1_max": A_op1_max,
        "A_op1_max_fmt": _u_fmt_num(A_op1_max),
        "A_op2_max": A_op2_max,
        "A_op2_max_fmt": _u_fmt_num(A_op2_max),
        "tp1": tp1,
        "tp2": tp2,
        "area_pedida": area_pedida,
        "area_pedida_fmt": _u_fmt_num(area_pedida),
        "A_considerada": A_considerada,
        "A_considerada_fmt": _u_fmt_num(A_considerada),
        "excedeu_area": excedeu_area,
        "to_projeto_pct": to_projeto_pct,
        "to_projeto_pct_fmt": _u_fmt_pct(to_projeto_pct),
        "A_livre": A_livre,
        "A_livre_fmt": _u_fmt_num(A_livre),
        "A_impermeavel_possivel": A_impermeavel_possivel,
        "A_impermeavel_possivel_fmt": _u_fmt_num(A_impermeavel_possivel),
        "A_ia_saldo": A_ia_saldo,
        "A_ia_saldo_fmt": _u_fmt_num(A_ia_saldo),
        "zone_title": zone_title,
        "desc": desc,
        "zone_class": zone_class,
        "via_class": via_class,
        "via_norm": via_norm,
        "zone_class_nome": _mf_sigla_nome(zone_class) if zone_class else "",
        "via_class_nome": _mf_sigla_nome(via_class) if via_class else "",
        "icon": icon,
        "status_curto": status_curto,
        "explicacao": explicacao,
        "pav_est": pav_est,
        "fmt_num": _u_fmt_num,
        "fmt_pct": _u_fmt_pct,
        "md_table": _u_md_table,
        "st": st,
        "render_figuras_anexo_v": render_figuras_anexo_v,
    }
    render_unifamiliar_items(unifamiliar_ctx)

    with st.expander("Ver regra completa (JSON)"):
        st.json(rule)
