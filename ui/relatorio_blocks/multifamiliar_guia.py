from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, List

import math
import streamlit as st


def _get_supabase():
    try:
        from core.supabase_client import get_supabase  # type: ignore
        return get_supabase()
    except Exception:
        return None


def _norm(s: Any) -> str:
    return str(s or "").strip().upper()

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


def _pct_rule(v: Any) -> Optional[float]:
    try:
        if v is None or v == "":
            return None
        f = float(v)
        return f * 100 if 0 <= f <= 1 else f
    except Exception:
        return None



def _sigla_nome(sigla: str) -> str:
    s = _norm(sigla)
    mapa = {
        "A": "Adequado",
        "I": "Inadequado",
        "AP": "Adequado (pequeno porte)",
        "AM": "Adequado (médio porte)",
        "AP/AM": "Depende do porte (pequeno/médio)",
        "PE": "Projeto especial",
    }
    return mapa.get(s, "")


def _zone_candidates(z: str) -> List[str]:
    """Gera variações para bater com possíveis formatos do banco (ex.: 'ZEPE 1' vs 'ZEPE1')."""
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
    return None  # via local / outras não entram na tabela por tipo de via



def _summarize_adequabilidade(*, zone_class: str | None, via_norm: str | None, via_class: str | None) -> tuple[str, str, str]:
    """Resumo final (bem leigo) para a adequabilidade."""
    z = _norm(zone_class)
    v = _norm(via_class)

    # Via local / sem tabela por tipo de via
    if not via_norm:
        if z == "I":
            return ("❌", "NÃO PERMITE", "A zona indicou I (Inadequado / não permitido). Em via local, normalmente vale a regra da zona.")
        if z == "AP/AM":
            return ("⚠️", "DEPENDE DO PORTE", "A zona indicou AP/AM (depende do porte). Em via local, normalmente vale a regra da zona.")
        if z == "PE":
            return ("⚠️", "PROJETO ESPECIAL", "A zona indicou PE (Projeto especial). Pode exigir análise/condições extras no licenciamento.")
        if z in ("A", "AP", "AM"):
            return ("✅", "PERMITE", "A zona permite. Ainda é obrigatório cumprir TO/TP/IA/recuos/altura e demais exigências.")
        return ("⚠️", "SEM DADO", "Não foi possível determinar o resultado por zona.")

    # Via entra na tabela (arterial/coletora/paisagística)
    if v == "I":
        return ("❌", "NÃO PERMITE", "O tipo de via indicou I (não permitido), mesmo que a zona permita.")
    if z == "I" and v in ("A", "AP", "AM"):
        return ("⚠️", "POSSÍVEL PELA VIA", "A zona deu I, mas o tipo de via permite. O licenciamento pode considerar o resultado por tipo de via.")
    if z == "I" and v == "AP/AM":
        return ("⚠️", "DEPENDE DO PORTE", "A zona deu I, mas o tipo de via deu AP/AM (depende do porte). Pode depender do licenciamento.")
    if z == "I" and v == "PE":
        return ("⚠️", "PROJETO ESPECIAL", "A zona deu I, mas o tipo de via indica PE (Projeto especial). Pode exigir análise/condições extras.")
    if z == "AP/AM" or v == "AP/AM":
        return ("⚠️", "DEPENDE DO PORTE", "Existe indicação AP/AM (depende do porte). Confira se o empreendimento é pequeno ou médio.")
    if z == "PE" or v == "PE":
        return ("⚠️", "PROJETO ESPECIAL", "Existe indicação PE (Projeto especial). Pode exigir análise/condições extras no licenciamento.")
    return ("✅", "PERMITE", "Zona e/ou tipo de via permitem. Ainda é obrigatório cumprir TO/TP/IA/recuos/altura e demais exigências.")
def _fetch_adequabilidade(
    *, zone_sigla: str, via_tipo_texto: Optional[str], use_type_code: str
) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
    """Busca adequabilidade por zona (2A) e por tipo de via (arterial/coletora)."""
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

    # Zona (Quadro 2A - sede)
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

    # Tipo de via (arterial/coletora) — quando aplicável
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



def _tipo_multifamiliar_label(multi_tipo: str, use_type_code: str) -> str:
    if multi_tipo in ("R21", "R2.1", "R2_1") or use_type_code.endswith("R21"):
        return "R2.1 — 2 unidades no mesmo lote (justapostas ou sobrepostas)"
    if multi_tipo in ("R22", "R2.2", "R2_2") or use_type_code.endswith("R22"):
        return "R2.2 — condomínio horizontal"
    if multi_tipo in ("R3", "R03") or use_type_code.endswith("R3"):
        return "R3 — condomínio vertical"
    return "Residência multifamiliar"


def render_multifamiliar_guia(*, calc: Dict[str, Any], rule: Optional[Dict[str, Any]] = None, **_: Any) -> None:
    from .quadro_tecnico import render_quadro_tecnico
    from .figuras_anexo_v import render_figuras_anexo_v

    multi_tipo = _norm(calc.get("multi_tipo"))
    use_type_code = _norm(calc.get("use_type_code"))
    zona = _norm(calc.get("zone") or calc.get("zone_sigla"))
    via = calc.get("via_nome") or calc.get("street_name") or "—"
    via_tipo_txt = calc.get("via_tipo") or calc.get("via_type") or ""
    subzona = calc.get("subzone_code") or (rule or {}).get("subzone_code") or "PADRAO"
    zone_label = calc.get("zone") or calc.get("zone_label_raw") or zona
    lot_area = calc.get("lot_area_m2")
    lot_front = calc.get("lot_front_m") or calc.get("front_m") or 0
    lot_depth = calc.get("lot_depth_m") or calc.get("depth_m") or 0
    is_corner = bool(st.session_state.get("lot_is_corner") or False)
    tipo_lote = "Esquina" if is_corner else "Meio de quadra"
    uso_label = _tipo_multifamiliar_label(multi_tipo, use_type_code)

    try:
        lot_area_f = float(lot_area) if lot_area not in (None, "", "-") else None
    except Exception:
        lot_area_f = None

    zone_class, via_class, dbg = _fetch_adequabilidade(
        zone_sigla=zona,
        via_tipo_texto=via_tipo_txt,
        use_type_code=use_type_code,
    )
    via_norm = _via_tipo_norm(via_tipo_txt)
    icon, status_curto, explicacao = _summarize_adequabilidade(zone_class=zone_class, via_norm=via_norm, via_class=via_class)

    try:
        from core.zone_descriptions import fetch_zone_description
        desc = fetch_zone_description(str(zona or ""), str(subzona or "PADRAO"), str(zone_label or ""))
    except Exception:
        desc = None

    if rule and isinstance(rule, dict) and lot_area_f and lot_area_f > 0:
        to_max_pct = _pct_rule(rule.get("to_max_pct")) or _pct_rule(rule.get("to_max"))
        tp_min_pct = _pct_rule(rule.get("tp_min_pct")) or _pct_rule(rule.get("tp_min"))
        ia_max = rule.get("ia_max")
        ia_min = rule.get("ia_min")
        try:
            ia_max_f = float(ia_max) if ia_max not in (None, "") else None
        except Exception:
            ia_max_f = None

        to_m2 = lot_area_f * (to_max_pct / 100.0) if isinstance(to_max_pct, (int, float)) else None
        tp_m2 = lot_area_f * (tp_min_pct / 100.0) if isinstance(tp_min_pct, (int, float)) else None
        ia_m2 = lot_area_f * ia_max_f if ia_max_f is not None else None

        gabarito = rule.get("gabarito_m") or rule.get("altura_max_m")
        try:
            gabarito_f = float(gabarito) if gabarito not in (None, "") else None
        except Exception:
            gabarito_f = None
        pav_est = max(1, int(math.floor(gabarito_f / 3.0))) if gabarito_f else None

        rec_fr = _pct_rule(None)  # noop for typing
        try:
            rec_fr = float(rule.get("recuo_frontal_m")) if rule.get("recuo_frontal_m") not in (None, "") else None
        except Exception:
            rec_fr = None
        try:
            rec_lat = float(rule.get("recuo_lateral_m")) if rule.get("recuo_lateral_m") not in (None, "") else None
        except Exception:
            rec_lat = None
        try:
            rec_fun = float(rule.get("recuo_fundos_m")) if rule.get("recuo_fundos_m") not in (None, "") else None
        except Exception:
            rec_fun = None

        area_min = rule.get("area_lote_min_m2") or rule.get("lote_min_area_m2")
        testada_min = rule.get("testada_min_m")

        W = float(lot_front or 0) if lot_front not in (None, "") else 0.0
        D = float(lot_depth or 0) if lot_depth not in (None, "") else 0.0
        W_util = None
        D_util = None
        A_recuos = None
        if rec_lat is not None and rec_fr is not None and rec_fun is not None and W > 0 and D > 0:
            W_util = W - 2 * rec_lat
            D_util = D - rec_fr - rec_fun
            if W_util > 0 and D_util > 0:
                A_recuos = W_util * D_util

        tp_rest_to = (lot_area_f - to_m2) if (lot_area_f and to_m2 is not None) else None
        tp_imperm_to = (tp_rest_to - tp_m2) if (tp_rest_to is not None and tp_m2 is not None) else None

        tp_rest_recuos = (lot_area_f - A_recuos) if (lot_area_f and A_recuos is not None) else None
        tp_imperm_recuos = (tp_rest_recuos - tp_m2) if (tp_rest_recuos is not None and tp_m2 is not None) else None
    else:
        to_max_pct = tp_min_pct = ia_max = ia_min = to_m2 = tp_m2 = ia_m2 = gabarito_f = pav_est = None
        rec_fr = rec_lat = rec_fun = area_min = testada_min = None
        W = D = 0.0
        W_util = D_util = A_recuos = None
        tp_rest_to = tp_imperm_to = tp_rest_recuos = tp_imperm_recuos = None

    st.markdown("## 🏢 RELATÓRIO URBANÍSTICO — MULTIFAMILIAR")
    st.markdown(
        "Este relatório mostra, de forma simples, se o uso residencial multifamiliar pode ou não ser desenvolvido neste terreno, "
        "com base na zona, na via e nas regras urbanísticas do município.\n\n"
        "A ideia aqui é facilitar a leitura: primeiro mostramos onde o terreno está localizado, depois se o uso é viável, "
        "em seguida explicamos os principais limites urbanísticos e, por fim, trazemos os pontos mais importantes "
        "do tipo multifamiliar escolhido.\n\n"
        "**Importante:** este relatório é uma análise inicial. A aprovação final depende da conferência completa no licenciamento."
    )

    st.markdown("---\n### 📍 1️⃣ Onde está localizado o terreno?")
    st.markdown("Aqui estão os dados principais usados nesta análise:")
    st.markdown(
        f"- **Uso informado:** {uso_label}\n"
        f"- **Área do terreno:** {_fmt_num(lot_area_f)} m²\n"
        f"- **Dimensões:** {_fmt_num(lot_front)} m × {_fmt_num(lot_depth)} m\n"
        f"- **Zona:** {zona or '—'}\n"
        f"- **Subzona / setor:** {subzona}\n"
        f"- **Tipo de lote:** {tipo_lote}\n"
        f"- **Via:** {via}\n"
        f"- **Tipo de via:** {via_tipo_txt or '—'}"
    )
    st.markdown("Essas informações são a base de todo o relatório.")

    if multi_tipo in ("R21", "R2.1", "R2_1") or use_type_code.endswith("R21"):
        st.markdown("---\n### 🏘️ O que é o residencial multifamiliar R2.1?")
        st.markdown(
            "É o caso em que existem **2 unidades habitacionais no mesmo lote**, podendo ser:\n\n"
            "- **justapostas** → residências lado a lado (**horizontal**)\n"
            "- **sobrepostas** → uma unidade embaixo e outra em cima"
        )

    st.markdown("---\n### ✅ 2️⃣ O uso residencial multifamiliar é viável neste terreno?")
    if not zone_class and not via_class:
        st.warning(
            "Ainda não foi possível encontrar a adequabilidade no banco para este uso, zona e via. "
            "Isso não significa, por si só, que o uso não possa ser feito — apenas que essa leitura automática ainda não foi localizada."
        )
        with st.expander("🔎 Diagnóstico (para conferência)"):
            st.json(dbg)
    else:
        st.markdown(
            "No multifamiliar, a permissão pode depender da **zona** e, em alguns casos, também do **tipo da via**. "
            "Por isso, o resultado abaixo mostra essas duas leituras de forma separada."
        )
        via_line = f"- **Por via:** {via_class} ({_sigla_nome(via_class)})" if via_norm and via_class else (
            f"- **Por via:** {via_tipo_txt or 'via local'}" if not via_norm else "- **Por via:** não encontrado"
        )
        st.markdown(
            f"- **Por zona:** {zone_class or 'não encontrado'}"
            + (f" ({_sigla_nome(zone_class)})" if zone_class else "")
            + "\n"
            + via_line
            + f"\n- **Resumo final:** {icon} **{status_curto}**"
        )
        if status_curto == "PERMITE":
            st.success(f"{icon} **Resumo final: {status_curto}.** {explicacao}")
        elif status_curto in ("DEPENDE DO PORTE", "PROJETO ESPECIAL", "VIA PODE INFLUENCIAR"):
            st.warning(f"{icon} **Resumo final: {status_curto}.** {explicacao}")
        else:
            st.error(f"{icon} **Resumo final: {status_curto}.** {explicacao}")

    st.markdown("---\n### 🧭 3️⃣ O que essa zona permite neste terreno?")
    st.markdown(
        "Toda zona tem suas próprias regras. No multifamiliar, ela ajuda a definir o que pode ser construído, "
        "quanto pode ocupar no térreo, quanto precisa ficar livre e qual o porte mais adequado do empreendimento."
    )
    if desc and desc.get("description_text"):
        title = str(desc.get("title") or zona).strip()
        if title.upper() == (zona or "").upper():
            zone_head = zona
        elif title.upper().startswith((zona or "").upper() + " —") or title.upper().startswith((zona or "").upper() + " -"):
            zone_head = title
        else:
            zone_head = f"{zona} — {title}"
        st.markdown(f"**{zone_head}**")
        st.markdown(str(desc.get("description_text")))
    else:
        st.markdown(
            f"- **Zona:** {zona or '—'}\n"
            f"- **Via do terreno:** {via}\n"
            f"- **Tipo de via:** {via_tipo_txt or '—'}"
        )
        st.markdown("Em alguns casos, a via também influencia essa leitura, principalmente fora da via local.")

    st.markdown("---\n### 📘 4️⃣ Como funciona a leitura da adequabilidade no multifamiliar?")
    st.markdown(
        "No multifamiliar, a análise não depende só do nome da zona. Em alguns casos, também é preciso olhar "
        "o **porte do empreendimento** e o **tipo da via**. As siglas abaixo ajudam a entender melhor o resultado mostrado acima."
    )
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**O que significam as siglas (bem simples):**")
        st.markdown(
            "| Sigla | O que significa | Como interpretar |\n"
            "|---|---|---|\n"
            "| **A** | Adequado / permitido | Pode seguir com o projeto, respeitando as demais regras. |\n"
            "| **I** | Inadequado / não permitido | Em regra, não pode nesse local/condição. |\n"
            "| **AP** | Adequado (pequeno porte) | Pode, mas normalmente limitado a porte pequeno. |\n"
            "| **AM** | Adequado (médio porte) | Pode, mas normalmente limitado a porte médio. |\n"
            "| **AP/AM** | Depende do porte | Pode, mas depende se o caso é pequeno ou médio. |\n"
            "| **PE** | Projeto especial | Pode exigir análise específica e condições extras no licenciamento. |"
        )
    with col2:
        st.markdown("**O que é “porte” (pequeno / médio / grande)?**")
        st.caption("Porte é a escala do empreendimento, normalmente definida pela área construída total (m²).")
        st.markdown(
            "| Porte | Faixa (área construída total) |\n"
            "|---|---|\n"
            "| **Pequeno** | até **250 m²** |\n"
            "| **Médio** | de **250,01 m²** até **1.000 m²** |\n"
            "| **Grande** | de **1.000,01 m²** até **5.000 m²** |\n"
            "| **Projeto especial** | acima de **5.000 m²** |"
        )

    st.markdown("---\n### 📏 5️⃣ Regras principais para este terreno")
    st.markdown("Depois de entender se o uso é permitido, o próximo passo é ver os limites básicos do lote para começar o estudo.")
    if not rule:
        st.warning(
            "Ainda não temos uma regra específica do multifamiliar carregada do Supabase para esta zona. "
            "Por isso, os próximos limites precisam ser confirmados diretamente no licenciamento e nos anexos da lei."
        )
    else:
        st.markdown(
            f"- **TO máxima:** {_fmt_pct(to_max_pct)}\n"
            f"- **TP mínima:** {_fmt_pct(tp_min_pct)}\n"
            f"- **IA máximo:** {_fmt_num(ia_max, 2) if ia_max not in (None, '') else '—'}\n"
            f"- **IA mínimo:** {_fmt_num(ia_min, 2) if ia_min not in (None, '') else 'não informado'}\n"
            f"- **Recuo frontal:** {_fmt_num(rec_fr)} m\n"
            f"- **Recuo lateral:** {_fmt_num(rec_lat)} m\n"
            f"- **Recuo de fundos:** {_fmt_num(rec_fun)} m\n"
            f"- **Altura permitida máxima da zona:** {_fmt_num(gabarito_f)} m\n"
            f"- **Testada mínima:** {_fmt_num(testada_min)} m\n"
            f"- **Área mínima do lote:** {_fmt_num(area_min)} m²"
        )

    st.markdown("---\n### 📐 6️⃣ Quanto posso ocupar no térreo?")
    if to_max_pct is None or to_m2 is None:
        st.info("Ainda não foi possível calcular a Taxa de Ocupação com base na regra carregada.")
    else:
        st.markdown(
            f"A zona permite ocupar até **{_fmt_pct(to_max_pct)}** do terreno no térreo.\n\n"
            f"👉 **{_fmt_num(lot_area_f)} m² × {_fmt_pct(to_max_pct)} = {_fmt_num(to_m2)} m²**\n\n"
            "Esse é o limite máximo permitido pela Taxa de Ocupação (TO).\n\n"
            "Mas, na prática, o que realmente cabe no térreo depende também dos **recuos exigidos**, da **forma do lote** e do **tipo multifamiliar analisado**."
        )
        if rec_fr is not None or rec_lat is not None or rec_fun is not None:
            st.markdown(
                f"**Recuos da zona:**\n"
                f"- Frontal: {_fmt_num(rec_fr)} m\n"
                f"- Laterais: {_fmt_num(rec_lat)} m\n"
                f"- Fundo: {_fmt_num(rec_fun)} m"
            )
        if A_recuos is not None and W_util is not None and D_util is not None:
            st.markdown(
                f"**Leitura com os recuos da zona:**\n\n"
                f"Largura útil: **{_fmt_num(W_util)} m**\n"
                f"Profundidade útil: **{_fmt_num(D_util)} m**\n\n"
                f"👉 **{_fmt_num(W_util)} × {_fmt_num(D_util)} = {_fmt_num(A_recuos)} m²**"
            )
        if multi_tipo in ("R21", "R2.1", "R2_1") or use_type_code.endswith("R21"):
            st.markdown(
                "**Parâmetros urbanísticos no caso justaposto**\n\n"
                "Quando a zona permitir, o multifamiliar justaposto pode usar os parâmetros do **unifamiliar**, respeitando a adequabilidade.\n\n"
                "**Exemplo prático:** em um caso de **R2.1 justaposto**, quando a zona admitir essa leitura, o projeto pode seguir os parâmetros do **unifamiliar** para ocupação e recuos, sempre respeitando a adequabilidade e verificando a **Taxa de Ocupação (TO)** e a **Taxa de Permeabilidade (TP)**."
            )

    st.markdown("---\n### 🌿 7️⃣ Quanto preciso deixar livre?")
    if tp_min_pct is None or tp_m2 is None:
        st.info("Ainda não foi possível calcular a Taxa de Permeabilidade com base na regra carregada.")
    else:
        st.markdown(
            f"A zona exige **{_fmt_pct(tp_min_pct)}** de área permeável.\n\n"
            f"👉 **{_fmt_num(lot_area_f)} m² × {_fmt_pct(tp_min_pct)} = {_fmt_num(tp_m2)} m²** obrigatórios permeáveis\n\n"
            "Isso quer dizer que parte do terreno precisa continuar permitindo a infiltração da água da chuva no solo."
        )
        if to_m2 is not None and tp_rest_to is not None and tp_imperm_to is not None:
            st.markdown(
                "**Cenário pelo máximo da TO:**\n\n"
                f"Se você utilizar **{_fmt_num(to_m2)} m²** no térreo:\n\n"
                f"👉 Área restante no lote: **{_fmt_num(lot_area_f)} m² − {_fmt_num(to_m2)} m² = {_fmt_num(tp_rest_to)} m²**\n\n"
                f"Desses, **{_fmt_num(tp_m2)} m²** devem permitir infiltração no solo e **{_fmt_num(tp_imperm_to)} m²** podem receber piso impermeável."
            )
        if A_recuos is not None and tp_rest_recuos is not None and tp_imperm_recuos is not None:
            st.markdown(
                "**Cenário usando a implantação pelos recuos da zona:**\n\n"
                f"Se você utilizar **{_fmt_num(A_recuos)} m²** no térreo:\n\n"
                f"👉 Área restante no lote: **{_fmt_num(lot_area_f)} m² − {_fmt_num(A_recuos)} m² = {_fmt_num(tp_rest_recuos)} m²**\n\n"
                f"Desses, **{_fmt_num(tp_m2)} m²** devem permitir infiltração no solo e **{_fmt_num(tp_imperm_recuos)} m²** podem receber piso impermeável."
            )
        st.markdown(
            "👉 **Leitura prática:** quanto maior a ocupação e a impermeabilização do terreno, menor fica a área disponível para atender a permeabilidade mínima exigida pela zona."
        )

    st.markdown("---\n### 🏢 8️⃣ Posso construir mais andares?")
    if ia_max in (None, "") or ia_m2 is None:
        st.info("Ainda não foi possível calcular o potencial total de construção com base no IA da zona.")
    else:
        st.markdown(
            f"Além do limite no térreo, existe o limite total permitido.\n\n"
            f"**Índice de Aproveitamento (IA):** {_fmt_num(ia_max, 2)}\n\n"
            f"👉 **{_fmt_num(lot_area_f)} m² × {_fmt_num(ia_max, 2)} = {_fmt_num(ia_m2)} m²** no total\n\n"
            f"Isso significa que a construção pode chegar até **{_fmt_num(ia_m2)} m²** somando todos os pavimentos.\n\n"
            f"**Altura permitida máxima da zona:** {_fmt_num(gabarito_f)} m"
        )
        if pav_est:
            st.markdown(
                f"\n\n**Estimativa simples para ter noção do número de pavimentos**\n\n"
                f"Se você adotar um pé-direito médio de **3,00 m por pavimento**, essa altura pode permitir, em média, algo próximo de **{pav_est} pavimentos**.\n\n"
                "👉 Isso é apenas uma referência inicial. Na prática, a quantidade real de andares depende também da laje, cobertura, platibanda, caixa d’água e da forma como o projeto será desenvolvido."
            )

    st.markdown("---\n### 🔎 9️⃣ O que preciso observar no tipo multifamiliar escolhido?")
    if multi_tipo in ("R21", "R2.1", "R2_1") or use_type_code.endswith("R21"):
        st.markdown("**R2.1 — 2 unidades no mesmo lote (justapostas ou sobrepostas)**")
        st.markdown(
            "- ✅ **Altura/andares:** pode ter no máximo 2 pavimentos.\n"
            "- ✅ **Justapostas (lado a lado):** testada mínima 8,00 m (exceto ZEIS).\n"
            "- ✅ **Parâmetros urbanísticos:** quando a zona permitir, pode usar os parâmetros do **unifamiliar**, respeitando a adequabilidade."
        )
    elif multi_tipo in ("R22", "R2.2", "R2_2") or use_type_code.endswith("R22"):
        st.markdown("**R2.2 — condomínio horizontal**")
        st.markdown(
            "- ✅ **Organização:** unidades com acesso por via interna.\n"
            "- ✅ **Acesso de veículos:** abertura mínima 4,00 m de largura e 4,50 m de altura livre.\n"
            "- ✅ **Via interna:** largura mínima 6,00 m.\n"
            "- ✅ **Áreas comuns:** prever circulação, acessibilidade e áreas de apoio.\n"
            "- ⚠️ **Quadra máxima:** esse ponto deve ser conferido conforme a zona."
        )
    elif multi_tipo in ("R3", "R03") or use_type_code.endswith("R3"):
        st.markdown("**R3 — residência multifamiliar vertical**")
        st.markdown(
            "- ✅ **Tipologia:** edifício ou condomínio vertical.\n"
            "- ✅ **Atenção:** altura, circulação, áreas comuns, vagas e acessos fazem parte da análise.\n"
            "- ⚠️ **Quadra máxima:** esse ponto também deve ser conferido conforme a zona."
        )
    else:
        st.info("Selecione o tipo de multifamiliar para exibir o checklist específico.")

    st.markdown("---\n### 🚗 🔟 Preciso de vagas de estacionamento?")
    st.markdown("No multifamiliar, a quantidade de vagas depende do tamanho do apartamento (área construída da unidade).")
    st.markdown(
        "- 🚗 **Apartamento com menos de 90 m²** → 1 vaga por unidade\n"
        "- 🚗 **Apartamento com 90 m² ou mais** → 1,5 vaga por unidade"
    )
    st.success("📌 Quando aparecer 1,5, o total final deve ser arredondado para cima (não existe meia vaga).")
    st.markdown("**Exemplos rápidos:**")
    st.markdown(
        "- 10 apartamentos com 80 m² → 10 vagas\n"
        "- 11 apartamentos com 100 m² → 11 × 1,5 = 16,5 → 17 vagas"
    )
    st.info("**Informação importante:** Art. 121, § 4º: “Poderá ser utilizada até 30% (trinta por cento) das vagas de estacionamento previstas para estacionamento de motocicletas.”")

    st.markdown("---\n### 📋 1️⃣1️⃣ Quais medidas mínimas os ambientes precisam ter?")
    st.markdown(
        "Além das regras do lote, a legislação também traz medidas mínimas para alguns ambientes da edificação. "
        "Isso vale para itens como sala, quartos, cozinha, banheiro, área de serviço, garagem e escada."
    )
    render_quadro_tecnico()

    st.markdown("---\n### 🚶 1️⃣2️⃣ O que preciso saber sobre a calçada?")
    st.markdown(
        "A análise não termina dentro do lote. Também existem regras para calçada, acesso ao imóvel, rebaixo de meio-fio e relação do lote com a rua. "
        "As figuras abaixo ajudam a visualizar esse padrão."
    )
    render_figuras_anexo_v(rule or {})

    st.markdown("---\n### 💡 1️⃣3️⃣ Dicas valiosas")
    if multi_tipo in ("R21", "R2.1", "R2_1") or use_type_code.endswith("R21"):
        st.markdown(
            "**Parâmetros do unifamiliar no caso justaposto**\n\n"
            "Quando a zona permitir, o multifamiliar justaposto pode usar os parâmetros do **unifamiliar**, respeitando a adequabilidade.\n\n"
            "**Exemplo prático:** em um caso de **R2.1 justaposto**, quando a zona admitir essa leitura, o projeto pode seguir os parâmetros do **unifamiliar** para ocupação e recuos, sempre respeitando a adequabilidade e verificando a **Taxa de Ocupação (TO)** e a **Taxa de Permeabilidade (TP)**."
        )
    if multi_tipo in ("R22", "R2.2", "R2_2", "R3", "R03") or use_type_code.endswith(("R22", "R3")):
        st.markdown(
            "\n\n**Quadra máxima em R2.2 e R3**\n\n"
            "Para projetos multifamiliares **R2.2** e **R3**, a legislação menciona uma verificação relacionada à **quadra máxima da zona**. "
            "Em caso de dúvida, essa conferência deve ser feita no licenciamento e nos anexos da lei."
        )
    st.markdown(
        "\n\n**Passeios (calçadas)**\n\n"
        "Não há, na legislação municipal, uma medida única e fixa para a largura dos passeios. Quando existir, deve-se adotar o padrão definido no projeto aprovado do loteamento e/ou nas diretrizes urbanísticas da via; na ausência dessa previsão, utiliza-se como referência o passeio já implantado no logradouro."
    )
    st.markdown(
        "\n\n**Piscina, caixa d’água, cisterna e tanques**\n\n"
        "**Atenção:** para a Taxa de Ocupação (TO), a piscina não é contada como área construída do lote.\n\n"
        "**Art. 144.** As piscinas, espelhos d’água, caixas d’água, cisternas e tanques deverão observar um afastamento mínimo de **0,50 m** de todas as divisas do terreno e devem ser computados como **área impermeável** para o cálculo da Taxa de Permeabilidade.\n\n"
        "👉 **Na prática:** além de respeitar esse afastamento mínimo de **50 cm**, esses elementos também entram no cálculo da **TP** como área impermeável."
    )

    st.markdown("---\n### 📌 1️⃣4️⃣ Resumo rápido final")
    st.markdown("Se você quiser ver só o essencial deste terreno, este é o resumo principal:")
    st.markdown(
        f"- **Uso analisado:** {uso_label}\n"
        f"- **Zona:** {zona or '—'}\n"
        f"- **Tipo de lote:** {tipo_lote}\n"
        f"- **Via:** {via}\n"
        f"- **Tipo de via:** {via_tipo_txt or '—'}\n"
        f"- **Resultado final:** {icon} {status_curto}\n"
        f"- **TO máxima:** {_fmt_pct(to_max_pct)}\n"
        f"- **TP mínima:** {_fmt_pct(tp_min_pct)}\n"
        f"- **IA máximo:** {_fmt_num(ia_max, 2) if ia_max not in (None, '') else '—'}\n"
        f"- **Altura permitida máxima:** {_fmt_num(gabarito_f)} m"
    )

    st.markdown("---\n### ✅ 1️⃣5️⃣ Fechamento final")
    st.markdown(
        "Este relatório foi pensado para ajudar você a entender o terreno de forma mais simples.\n\n"
        "Na etapa de projeto e aprovação, ainda será preciso conferir os detalhes completos no licenciamento."
    )
