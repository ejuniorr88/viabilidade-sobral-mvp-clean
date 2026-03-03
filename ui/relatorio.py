from __future__ import annotations

from typing import Any, Dict, Optional, Callable

import streamlit as st


def _to_float(v: Any) -> float:
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return 0.0
        # pt-BR / Excel style: 1.234,56
        s = s.replace(".", "").replace(",", ".")
        try:
            return float(s)
        except Exception:
            return 0.0
    try:
        return float(v)
    except Exception:
        return 0.0


def _as_float(x: Any) -> Optional[float]:
    try:
        if x is None or x == "":
            return None
        return float(x)
    except Exception:
        return None


def _fmt_m2(v: float) -> str:
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m²"


def _fmt_m(v: float) -> str:
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m"


def render_relatorio_section(
    calc: Optional[Dict[str, Any]] = None,
    lot_area: Any = None,
    testada: Any = None,
    profundidade: Any = None,
    built_ground: Any = None,
    area_permeavel_prevista: Any = None,
    pick_func: Optional[Callable[..., Any]] = None,
    **kwargs: Any,
) -> None:
    """Renderiza a seção de relatório.

    Compatível com chamadas antigas e novas:
    - render_relatorio_section(calc=...)
    - render_relatorio_section()  (mostra instrução até clicar em Calcular)
    """

    if calc is None:
        calc = kwargs.get("calc") or {}

    if pick_func is None:
        def pick_func_local(r: Any, *ks: str) -> Any:
            if not isinstance(r, dict):
                return None
            for k in ks:
                v = r.get(k)
                if v not in (None, ""):
                    return v
            return None
        pick_func = pick_func_local

    st.subheader("6) Relatório Urbanístico")

    if not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar o relatório.")
        return

    rule = calc.get("rule") or kwargs.get("rule")
    if not rule:
        st.info("Sem regra do Supabase — não é possível gerar relatório.")
        return

    # Preferir parâmetros explícitos; se não vierem, usar o que estiver no calc
    lot_area_f = _to_float(lot_area if lot_area is not None else calc.get("lot_area"))
    testada_f = _to_float(testada if testada is not None else calc.get("testada"))
    profund_f = _to_float(profundidade if profundidade is not None else calc.get("profundidade"))
    built_ground_f = _to_float(
        built_ground if built_ground is not None else calc.get("built_ground")
    )
    area_perm_f = _to_float(
        area_permeavel_prevista if area_permeavel_prevista is not None else calc.get("area_permeavel_prevista")
    )

    zone = calc.get("zone") or calc.get("zone_sigla") or "—"
    use_type = calc.get("use_type_code") or "—"
    via_tipo = (calc.get("street_info") or {}).get("tipo_via") or calc.get("via_tipo") or "via local"

    to_max = _as_float(pick_func(rule, "to_max_pct", "to_max"))
    ia_max = _as_float(pick_func(rule, "ia_max", "ia_maximo"))
    tp_min = _as_float(pick_func(rule, "tp_min_pct", "tp_min"))

    rec_frente = _as_float(pick_func(rule, "recuo_frontal_m", "front_setback_m", "recuo_frontal")) or 0.0
    rec_lateral = _as_float(pick_func(rule, "recuo_lateral_m", "side_setback_m", "recuo_lateral")) or 0.0
    rec_fundo = _to_float(pick_func(rule, "recuo_fundo_m", "recuo_fundos_m", "recuo_fundo", "recuo_fundos"))

    # Se não informar área pretendida, assumir máximo da TO
    if (built_ground_f <= 0) and (to_max is not None) and lot_area_f > 0:
        built_ground_f = (lot_area_f * to_max) / 100.0

    # ===== Cabeçalho =====
    st.markdown("🏡 **RELATÓRIO URBANÍSTICO**")
    st.markdown(f"**{use_type}**")

    st.write(f"**Terreno:** {_fmt_m2(lot_area_f)}")
    st.write(f"**Dimensões:** {_fmt_m(testada_f)} × {_fmt_m(profund_f)}")
    st.write(f"**Zona:** {zone}")
    st.write(f"**Tipo:** {via_tipo}")

    st.markdown("---")

    # ===== 1) Quanto posso ocupar no chão? =====
    st.markdown("📍 **1️⃣ Quanto posso ocupar no chão?**")

    if to_max is not None:
        max_to_area = (lot_area_f * to_max) / 100.0
        st.write(f"A zona permite ocupar até **{to_max:.0f}%** do terreno no térreo.")
        st.write(f"👉 {_fmt_m2(lot_area_f)} × {to_max:.0f}% = **{_fmt_m2(max_to_area)}**")
        st.write("Esse é o limite máximo permitido pela **Taxa de Ocupação (TO)**.")
    else:
        max_to_area = 0.0
        st.warning("TO máxima não encontrada na regra.")

    st.write("Agora veja duas situações possíveis:")

    # ===== Opção 1 =====
    st.markdown("✅ **Opção 1 – Respeitando os recuos padrão**")
    st.write("**Recuos exigidos:**")
    st.write(f"- Frontal: **{_fmt_m(rec_frente)}**")
    st.write(f"- Laterais: **{_fmt_m(rec_lateral)}** cada")
    st.write(f"- Fundo: **{_fmt_m(rec_fundo)}**")

    # Área interna disponível (aproximação retangular)
    largura_util = max(0.0, testada_f - (2 * rec_lateral))
    profund_util = max(0.0, profund_f - rec_frente - rec_fundo)
    area_interna = largura_util * profund_util

    st.write("**Área interna disponível:**")
    st.write(f"- Largura útil: {testada_f:,.2f} − {rec_lateral:,.2f} − {rec_lateral:,.2f} = **{largura_util:,.2f} m**".replace(",", "X").replace(".", ",").replace("X", "."))
    st.write(f"- Profundidade útil: {profund_f:,.2f} − {rec_frente:,.2f} − {rec_fundo:,.2f} = **{profund_util:,.2f} m**".replace(",", "X").replace(".", ",").replace("X", "."))
    st.write(f"🔺 {largura_util:,.2f} × {profund_util:,.2f} = **{_fmt_m2(area_interna)}**".replace(",", "X").replace(".", ",").replace("X", "."))

    if max_to_area > 0:
        st.write(
            f"👉 Nesse caso, o limite dos recuos permite até **{_fmt_m2(area_interna)}**, "
            f"mas o teto da TO limita em **{_fmt_m2(max_to_area)}**."
        )

    # (Mantemos o restante do relatório igual ao que já estava no arquivo original,
    # mas, se não existir, não quebramos.)
    # Para não perder nada do layout, renderizamos o restante se estiver presente no calc.
    extra_md = calc.get("relatorio_extra_md")
    if isinstance(extra_md, str) and extra_md.strip():
        st.markdown("---")
        st.markdown(extra_md)

    # Se TP mínima existir, calcular área permeável mínima e área estimada
    if tp_min is not None and lot_area_f > 0:
        st.markdown("---")
        st.markdown("🌱 **Área Permeável (TP)**")
        min_perm = (lot_area_f * tp_min) / 100.0
        st.write(f"Mínimo exigido: **{tp_min:.0f}%** → **{_fmt_m2(min_perm)}**")
        # Se usuário não informou permeável, estimar como “o que sobra” do térreo
        if area_perm_f <= 0 and lot_area_f > 0:
            area_perm_f = max(0.0, lot_area_f - built_ground_f)
            st.write(f"Estimativa automática (o que sobra do térreo): **{_fmt_m2(area_perm_f)}**")
        else:
            st.write(f"Informada: **{_fmt_m2(area_perm_f)}**")
        if area_perm_f + 1e-9 >= min_perm:
            st.success("✅ Atende à área permeável mínima.")
        else:
            st.error("❌ Não atende à área permeável mínima.")
