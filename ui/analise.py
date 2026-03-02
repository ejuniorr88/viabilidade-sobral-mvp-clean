from __future__ import annotations

from typing import Any, Dict, Optional, Callable

import streamlit as st


def _as_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        return float(x)
    except Exception:
        return None


def _pick(rule: Dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in rule and rule.get(k) is not None:
            return rule.get(k)
    return None


def _fmt_num(x: Any, nd: int = 2) -> str:
    if x is None:
        return "—"
    try:
        v = float(x)
        if abs(v - round(v)) < 1e-9:
            return str(int(round(v)))
        return f"{v:.{nd}f}"
    except Exception:
        return str(x)


def _pct(x: Any, nd: int = 1) -> str:
    if x is None:
        return "—"
    try:
        return f"{float(x):.{nd}f}%"
    except Exception:
        return "—"


def render_analise_section(
    *,
    calc: Dict[str, Any],
    lot_area: float,
    testada: float,
    profundidade: float,
    built_ground: float,
) -> None:
    """
    Seção 5) Análise Urbanística (Relatório em perguntas e respostas).

    Regras:
    - Só renderiza conteúdo completo se calc["ok"] e houver rule.
    - Usa somente dados que já existem no app (sem inventar índices).
    - Onde faltar dado (ex.: área permeável), pede input.
    """
    st.subheader("5) Análise Urbanística")

    if not calc.get("ok"):
        st.info("Clique em **Calcular viabilidade** para gerar a análise.")
        return

    rule = calc.get("rule")
    zone = calc.get("zone")
    use_type_code = calc.get("use_type_code") or "—"

    if not rule:
        st.info("Sem regra do Supabase — não é possível validar índices.")
        return

    # ---- índices principais
    to_max_pct = _as_float(_pick(rule, "to_max_pct", "to_max", "taxa_ocupacao_max_pct"))
    tp_min_pct = _as_float(_pick(rule, "tp_min_pct", "tp_min", "taxa_permeabilidade_min_pct"))
    ia_max = _as_float(_pick(rule, "ia_max", "ia_maximo", "indice_aproveitamento_max"))
    ia_min = _as_float(_pick(rule, "ia_min", "ia_minimo", "indice_aproveitamento_min"))
    altura_max_m = _as_float(_pick(rule, "altura_max_m", "gabarito_m", "altura_maxima_m", "altura_max"))

    rec_frente_m = _as_float(_pick(rule, "recuo_frontal_m", "recuo_frente_m", "recuo_frente"))
    rec_fundo_m = _as_float(_pick(rule, "recuo_fundo_m", "recuo_fundos_m", "recuo_fundo"))
    rec_lateral_m = _as_float(_pick(rule, "recuo_lateral_m", "recuo_lateral"))

    # ---- cálculos básicos
    ia_util = (built_ground / lot_area) if lot_area else 0.0
    to_util_pct = ((built_ground / lot_area) * 100.0) if lot_area else 0.0

    # permeável (precisa de input)
    st.markdown("### 🏡 RELATÓRIO URBANÍSTICO")
    st.markdown(f"**Uso:** {use_type_code}  \n**Terreno:** {_fmt_num(lot_area, 0)} m²  \n**Dimensões:** {_fmt_num(testada, 2)} m × {_fmt_num(profundidade, 2)} m  \n**Zona:** {zone or '—'}")

    st.divider()

    # 1) Ocupação no chão
    st.markdown("## 📍 1️⃣ Quanto posso ocupar no chão?")
    if to_max_pct is None:
        st.warning("A regra do Supabase não trouxe a **Taxa de Ocupação (TO) máxima** para este uso/zona.")
    else:
        max_ground = lot_area * (to_max_pct / 100.0)
        st.markdown(
            f"A zona permite ocupar até **{_pct(to_max_pct)}** do terreno no térreo.\n\n"
            f"👉 **{_fmt_num(lot_area,0)} m² × {_pct(to_max_pct)} = {_fmt_num(max_ground,2)} m²**"
        )
        st.markdown("Esse é o **limite máximo** pela Taxa de Ocupação.")
        st.markdown(f"**Você informou no térreo:** {_fmt_num(built_ground,2)} m²  \n**TO utilizada:** {_pct(to_util_pct)}")
        if to_util_pct <= to_max_pct:
            st.success("✅ A Taxa de Ocupação informada está dentro do permitido.")
        else:
            st.error("❌ A Taxa de Ocupação informada EXCEDE o permitido.")

    # Limite por recuos (quando houver)
    if rec_frente_m is not None and rec_fundo_m is not None and rec_lateral_m is not None:
        st.markdown("### ✅ Checagem do limite físico pelos recuos (estimativa)")
        largura_util = max(testada - 2 * rec_lateral_m, 0.0)
        prof_util = max(profundidade - rec_frente_m - rec_fundo_m, 0.0)
        area_util = largura_util * prof_util
        st.markdown(
            f"Recuos (regra): Frontal **{_fmt_num(rec_frente_m,2)} m**, Laterais **{_fmt_num(rec_lateral_m,2)} m**, Fundo **{_fmt_num(rec_fundo_m,2)} m**.\n\n"
            f"Largura útil: **{_fmt_num(testada,2)} − {_fmt_num(rec_lateral_m,2)} − {_fmt_num(rec_lateral_m,2)} = {_fmt_num(largura_util,2)} m**\n\n"
            f"Profundidade útil: **{_fmt_num(profundidade,2)} − {_fmt_num(rec_frente_m,2)} − {_fmt_num(rec_fundo_m,2)} = {_fmt_num(prof_util,2)} m**\n\n"
            f"📐 **{_fmt_num(largura_util,2)} × {_fmt_num(prof_util,2)} = {_fmt_num(area_util,2)} m²**\n\n"
            f"👉 Esse é um **teto físico estimado** (sem considerar pátios internos/recortes)."
        )
    else:
        st.info("Sem recuos completos no Supabase para estimar o limite físico do térreo.")

    st.divider()

    # 2) Permeabilidade
    st.markdown("## 🌿 2️⃣ Quanto preciso deixar livre (área permeável)?")
    if tp_min_pct is None:
        st.warning("A regra do Supabase não trouxe a **Taxa de Permeabilidade (TP) mínima** para este uso/zona.")
    else:
        area_perm_min = lot_area * (tp_min_pct / 100.0)
        st.markdown(
            f"A zona exige **{_pct(tp_min_pct)}** de área permeável.\n\n"
            f"👉 **{_fmt_num(lot_area,0)} m² × {_pct(tp_min_pct)} = {_fmt_num(area_perm_min,2)} m²** permeáveis (mínimo)."
        )

        area_perm_prev = st.number_input(
            "Informe a área permeável prevista no projeto (m²)",
            min_value=0.0,
            value=area_perm_min,
            step=1.0,
            key="area_permeavel_prevista_m2",
        )

        tp_prev_pct = (area_perm_prev / lot_area) * 100.0 if lot_area else 0.0
        st.markdown(f"**TP prevista:** {_pct(tp_prev_pct)}")
        if tp_prev_pct + 1e-9 >= tp_min_pct:
            st.success("✅ A Taxa de Permeabilidade atende ao mínimo.")
        else:
            st.error("❌ A Taxa de Permeabilidade está abaixo do mínimo.")

    st.divider()

    # 3) Área total / IA
    st.markdown("## 🏢 3️⃣ Quanto posso construir no total (IA)?")
    if ia_max is None:
        st.warning("A regra do Supabase não trouxe o **IA máximo** para este uso/zona.")
    else:
        area_total_max = lot_area * ia_max
        st.markdown(
            f"Índice de Aproveitamento (IA) máximo: **{_fmt_num(ia_max,2)}**\n\n"
            f"👉 **{_fmt_num(lot_area,0)} × {_fmt_num(ia_max,2)} = {_fmt_num(area_total_max,2)} m²** no total (somando todos os pavimentos)."
        )
        st.markdown(f"**IA utilizado (com base no térreo informado):** {_fmt_num(ia_util,2)}")
        if ia_util <= ia_max + 1e-9:
            st.success("✅ IA (com base no térreo) está dentro do máximo.")
        else:
            st.error("❌ IA (com base no térreo) EXCEDE o máximo.")

    if ia_min is not None:
        st.info(f"IA mínimo (regra): **{_fmt_num(ia_min,2)}** (quando aplicável).")

    if altura_max_m is not None:
        st.markdown(f"**Altura máxima da zona (gabarito):** {_fmt_num(altura_max_m,2)} m")

    st.divider()

    # 4) Estacionamento (placeholder)
    st.markdown("## 🚗 4️⃣ Estacionamento")
    st.info(
        "Nesta versão, o app ainda não calcula vagas automaticamente. "
        "Quando formos implementar, vamos ler o Anexo IV (vagas por atividade) e cruzar com o uso."
    )

    # Debug opcional
    with st.expander("Ver regra bruta (JSON do Supabase)", expanded=False):
        st.json(rule)
